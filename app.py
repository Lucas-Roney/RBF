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

# ── Interpolation logic ───────────────────────────────────────────────────────

x = np.linspace(-1, 1, 21)
f = 1 / (1 + 16 * x**2)
N = len(x)

def fillMatrix(e, rbf_name):
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

def run_interpolation(rbf_name, epsilon):        
    e = epsilon                                 

    c = fillMatrix(e, rbf_name)

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
        img = run_interpolation(rbf_name, epsilon) 
        return jsonify({"image": img})
    except np.linalg.LinAlgError:
        return jsonify({"error": "Singular matrix — try a different ε value."}), 400

# ── Error / best-epsilon logic ────────────────────────────────────────────────

def test_func(x_val):
    return 1 / (1 + 16 * (x_val ** 2))

def find_best_e(start, stop, rbf_name):
    rbf = RBF_MAP[rbf_name]
    x_vals = np.linspace(-1, 1, 1000)
    ideal_e = None
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

        error = 0.0
        for xv in x_vals:
            interp = sum(c[j] * rbf(abs(xv - x[j]), e) for j in range(N))
            err = abs(interp - test_func(xv))
            error += err

        error_vals[e] = error

        if error < min_error:
            min_error = error
            ideal_e = e

    return ideal_e, min_error, error_vals

def make_best_e_plots(rbf_name, start, stop):
    ideal_e, min_error, error_vals = find_best_e(start, stop, rbf_name)
    rbf = RBF_MAP[rbf_name]
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

    # ── Plot 2: Cumulative Error by ε ─────────────────────────────────────────
    x_e = list(error_vals.keys())
    y_e = list(error_vals.values())
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(x_e, y_e, c='k', zorder=1)
    sc = ax.scatter(x_e, y_e, c=y_e, cmap='RdYlGn_r', zorder=2)
    fig.colorbar(sc, label='Error Severity')
    ax.annotate(
        f"min error: {min_error:.3f}",
        xy=(ideal_e, min_error),
        xytext=(50, 0),
        textcoords='offset points',
        bbox=dict(boxstyle='round,pad=0.3', fc='w', alpha=0.3)
    )
    ax.set_title(f'Cumulative Error by ε  |  {rbf_name}')
    ax.set_xlabel('ε values')
    ax.set_ylabel('Cumulative error')
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
    start = float(data.get("start", 1))
    stop  = float(data.get("stop", 10))

    if rbf_name not in RBF_MAP:
        return jsonify({"error": "Unknown RBF"}), 400
    if start >= stop:
        return jsonify({"error": "Start must be less than stop."}), 400

    try:
        plots, ideal_e, min_error = make_best_e_plots(rbf_name, start, stop)
        return jsonify({**plots, "ideal_e": ideal_e, "min_error": round(min_error, 4)})
    except np.linalg.LinAlgError:
        return jsonify({"error": "Singular matrix in range — try different bounds."}), 400

if __name__ == '__main__':
    app.run(debug=True)