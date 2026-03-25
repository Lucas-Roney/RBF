from flask import Flask, render_template, request, jsonify
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# ── RBF definitions ───────────────────────────────────────────────────────────

def MQ(r, e):
    return np.sqrt(1 + (e * r) ** 2)

def IQ(r, e):
    return 1 / (1 + (e * r) ** 2)

def IMQ(r, e):
    return 1 / np.sqrt(1 + (e * r) ** 2)

def GA(r, e):
    return np.exp(-(e * r) ** 2)

RBF_MAP = {"MQ": MQ, "IQ": IQ, "IMQ": IMQ, "GA": GA}

# ── Test functions ───────────────────────────────────────────────────────────

def test_func1(x_val):
    return 1 / (1 + 16 * (x_val ** 2))

def test_func2(x_val):
    return np.tanh(10 * x_val)

def test_func3(x_val):
    return np.exp(x_val)

def test_func4(x_val):
    return abs(x_val)

FUNC_MAP = {"test_func1": test_func1, "test_func2": test_func2, "test_func3": test_func3, "test_func4": test_func4}

# ── Interpolation logic ───────────────────────────────────────────────────────

x = np.linspace(-1, 1, 21)
N = len(x)

def fillMatrix(e, rbf_name, f):
    rbf = RBF_MAP[rbf_name]
    A = np.zeros((N, N))          
    for i in range(N):
        for j in range(N):
            A[i, j] = rbf(abs(x[i] - x[j]), e) 
    c = np.linalg.solve(A, f)
    return c

def interpolate_point(x_val, e, c, rbf_name):    
    rbf = RBF_MAP[rbf_name]
    total = 0.0
    for j in range(N):
        total += c[j] * rbf(abs(x_val - x[j]), e)  
    return total

def run_interpolation(rbf_name, epsilon, func_name):     
    test_func = FUNC_MAP[func_name] 
    f = test_func(x)  
    e = epsilon                                 

    c = fillMatrix(e, rbf_name, f)

    x_vals = np.linspace(-1, 1, 300)
    y_vals = []
    for i in range(len(x_vals)):
        y_vals.append(interpolate_point(x_vals[i], e, c, rbf_name))  
    y_true = test_func(x_vals)

    fig, ax = plt.subplots(figsize=(7, 4))     
    ax.plot(x_vals, y_vals, c='k', label=f'RBF (ε = {e})', alpha=0.8)
    ax.plot(x_vals, y_true, c='r', linestyle=':', label='Test Function')
    ax.scatter(x, f, facecolors='none', edgecolors='k')
    ax.set_title(f'ε = {e}')
    ax.set_xlabel('x values')
    ax.set_ylabel('y values')
    ax.legend()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)     
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/interpolate", methods=["POST"])
def interpolate():
    data = request.get_json()
    rbf_name = data.get("rbf", "GA")
    epsilon  = float(data.get("epsilon", 5)) 

    if rbf_name not in RBF_MAP:
        return jsonify({"error": "Unknown RBF"}), 400

    try:
        func_name = data.get("func", "test_func1")
        img = run_interpolation(rbf_name, epsilon, func_name)
        return jsonify({"image": img})
    except np.linalg.LinAlgError:
        return jsonify({"error": "Singular matrix — try a different ε value."}), 400

@app.route("/interpolate_3d", methods=["POST"])
def interpolate_3d():
    data = request.get_json()
    epsilon = float(data.get("epsilon", 5))

    try:
        x_grid = np.linspace(-1, 1, 11)
        y_grid = np.linspace(-1, 1, 11)
        xx, yy = np.meshgrid(x_grid, y_grid)
        xx_flat = xx.flatten()
        yy_flat = yy.flatten()
        f = 1 / (1 + 16 * (xx_flat**2 + yy_flat**2))

        # Build and solve the system
        dx = xx_flat[:, None] - xx_flat[None, :]
        dy = yy_flat[:, None] - yy_flat[None, :]
        r  = np.sqrt(dx**2 + dy**2)
        A  = np.exp(-(epsilon * r)**2)
        c  = np.linalg.solve(A, f)

        # Evaluate on a fine grid for plotting
        x_plot = np.linspace(-1, 1, 100)
        y_plot = np.linspace(-1, 1, 100)
        xx_plot, yy_plot = np.meshgrid(x_plot, y_plot)
        xx_flat_plot = xx_plot.flatten()
        yy_flat_plot = yy_plot.flatten()

        dx2 = xx_flat_plot[:, None] - xx_flat[None, :]
        dy2 = yy_flat_plot[:, None] - yy_flat[None, :]
        r2  = np.sqrt(dx2**2 + dy2**2)
        z_vals = (np.exp(-(epsilon * r2)**2) @ c).reshape(xx_plot.shape)

        # Plot
        fig = plt.figure(figsize=(8, 6))
        ax  = fig.add_subplot(111, projection='3d')
        ax.plot_surface(xx_plot, yy_plot, z_vals, cmap='Spectral', alpha=0.8)
        ax.scatter(xx_flat, yy_flat, f, color='k', s=10)
        ax.set_title(f'ε = {epsilon}')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=120)
        plt.close(fig)
        buf.seek(0)
        return jsonify({"image": base64.b64encode(buf.read()).decode("utf-8")})

    except np.linalg.LinAlgError:
        return jsonify({"error": "Singular matrix — try a different ε value."}), 400

# ── Error / best-epsilon logic ────────────────────────────────────────────────

def find_best_e(start, stop, rbf_name, func_name):
    rbf = RBF_MAP[rbf_name]
    test_func = FUNC_MAP[func_name]
    f = test_func(x)
    x_vals = np.linspace(-1, 1, 1000)
    ideal_e = None
    max_error = float('-inf')
    min_error = float('inf')
    error_vals = {}

    for e in np.arange(start, stop, 0.1):
        e = round(float(e), 1)
        A = np.zeros((N, N))
        for i in range(N):
            for j in range(N):
                A[i, j] = rbf(abs(x[i] - x[j]), e)
        try:
            c = np.linalg.solve(A, f)
        except np.linalg.LinAlgError:
            continue

        max_error = float('-inf')
        for xv in x_vals:
            interp = sum(c[j] * rbf(abs(xv - x[j]), e) for j in range(N))
            err = abs(interp - test_func(xv))
            if err > max_error:
                max_error = err
        if max_error < min_error:
            min_error = max_error
            ideal_e = e

        error_vals[e] = max_error   

    return ideal_e, min_error, error_vals

def make_best_e_plots(rbf_name, func_name, start, stop):
    ideal_e, min_error, error_vals = find_best_e(start, stop, rbf_name, func_name)
    rbf = RBF_MAP[rbf_name]
    test_func = FUNC_MAP[func_name]
    f = test_func(x)
    x_vals = np.linspace(-1, 1, 1000)

    # Recompute interpolation at ideal_e
    A = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            A[i, j] = rbf(abs(x[i] - x[j]), ideal_e)
    c = np.linalg.solve(A, f)
    s = [sum(c[j] * rbf(abs(xv - x[j]), ideal_e) for j in range(N)) for xv in x_vals]
    y_true = test_func(x_vals)

    plots = {}

    # ── Plot 1: Interpolation vs Test Function ────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(x_vals, s, c='k', label=f'RBF (ε = {ideal_e})', alpha=0.8)
    ax.plot(x_vals, y_true, c='r', linestyle=':', label='Test Function')
    ax.scatter(x, f, facecolors='none', edgecolors='k', zorder=5, label='Data points')
    ax.set_title(f'Best ε Interpolation vs Test Function  |  {rbf_name}')
    ax.set_xlabel('x values')
    ax.set_ylabel('y values')
    ax.legend()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120)
    plt.close(fig)
    buf.seek(0)
    plots['interp'] = base64.b64encode(buf.read()).decode('utf-8')

    # ── Plot 2: Smallest Maximum Error by ε ─────────────────────────────────────────
    x_e = list(error_vals.keys())
    y_e = list(error_vals.values())
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(x_e, y_e, c='k', zorder=1)
    sc = ax.scatter(x_e, y_e, c=y_e, cmap='RdYlGn_r', zorder=2)
    fig.colorbar(sc, label='Error Severity')
    ax.plot([],[],' ', label=f"Min error: {round(min_error, 5)}")
    #ax.annotate(
    #    f"min error: {min_error:.3f}",
    #    xy=(ideal_e, min_error),
    #    xytext=(50, 0),
    #    textcoords='offset points',
    #    bbox=dict(boxstyle='round,pad=0.3', fc='w', alpha=0.3)
    #)
    ax.set_title(f'Max Residual Error by ε  |  {rbf_name}')
    ax.set_xlabel('ε values')
    ax.set_ylabel('Max Residual Error')
    ax.legend()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120)
    plt.close(fig)
    buf.seek(0)
    plots['cumulative_error'] = base64.b64encode(buf.read()).decode('utf-8')

    # ── Plot 3: Individual Error ──────────────────────────────────────────────
    individual_err = [
        sum(c[j] * rbf(abs(xv - x[j]), ideal_e) for j in range(N)) - test_func(xv)
        for xv in x_vals
    ]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(x_vals, individual_err, c='k')
    ax.set_title(f'Individual Error Values  |  {rbf_name}  |  ε = {ideal_e}')
    ax.set_xlabel('x values')
    ax.set_ylabel('Signed error')
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120)
    plt.close(fig)
    buf.seek(0)
    plots['individual_error'] = base64.b64encode(buf.read()).decode('utf-8')

    return plots, ideal_e, min_error


@app.route("/find_best_e", methods=["POST"])
def best_e_route():
    data = request.get_json()
    rbf_name = data.get("rbf", "GA")
    func_name = data.get("func", "test_func1")
    start = float(data.get("start", 1))
    stop  = float(data.get("stop", 10))

    if rbf_name not in RBF_MAP:
        return jsonify({"error": "Unknown RBF"}), 400
    if start >= stop:
        return jsonify({"error": "Start must be less than stop."}), 400

    try:
        plots, ideal_e, min_error = make_best_e_plots(rbf_name, func_name, start, stop)
        return jsonify({**plots, "ideal_e": ideal_e, "min_error": round(min_error, 4)})
    except np.linalg.LinAlgError:
        return jsonify({"error": "Singular matrix in range — try different bounds."}), 400

if __name__ == '__main__':
    app.run(debug=True)