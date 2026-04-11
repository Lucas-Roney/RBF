// ── Mode toggle (2D ↔ 3D) ─────────────────────────────────────────────────

const toggle3d = document.getElementById("toggle-3d");

toggle3d.addEventListener("change", () => {
    const is3d = toggle3d.checked;

    // Show/hide RBF selector
    document.getElementById("testFunc").style.display         = is3d ? "none" : "";
    document.getElementById("test-func-label").style.display  = is3d ? "none" : "";
    document.getElementById("func-display").style.display     = is3d ? "none" : "";

    // Swap tab bars
    document.getElementById("tabs-2d").style.display = is3d ? "none" : "flex";
    document.getElementById("tabs-3d").style.display = is3d ? "flex" : "none";

    // Reset to first tab
    if (is3d) {
        switchTab("3d");
    } else {
        switchTab("2d");
    }

    // Bold the active dim label
    document.getElementById("label-2d").classList.toggle("dim-active", !is3d);
    document.getElementById("label-3d").classList.toggle("dim-active",  is3d);
});

// ── Tab switching ─────────────────────────────────────────────────────────

const ALL_PANELS = ["2d", "3d", "best", "best3d"];

function switchTab(tab) {
    // Hide all panels
    ALL_PANELS.forEach(id => {
        document.getElementById(`panel-${id}`).style.display = "none";
    });

    // Show the chosen panel
    document.getElementById(`panel-${tab}`).style.display = "block";

    // Update active tab highlight — only touch the visible tab bar
    const is3d = toggle3d.checked;
    const barId = is3d ? "tabs-3d" : "tabs-2d";
    document.querySelectorAll(`#${barId} .tab`).forEach((btn, i) => {
        const targets = is3d ? ["3d", "best3d"] : ["2d", "best"];
        btn.classList.toggle("active", targets[i] === tab);
    });
}

// ── KaTeX function display ────────────────────────────────────────────────

const funcLatex = {
    test_func1: "\\frac{1}{1 + 16x^2}",
    test_func2: "\\frac{e^{10x} - e^{-10x}}{e^{10x} + e^{-10x}}",
    test_func3: "e^{x}",
    test_func4: "\\left|x\\right|",
};

function updateFuncDisplay() {
    const val = document.getElementById("testFunc").value;
    katex.render(funcLatex[val], document.getElementById("func-display"));
}

document.getElementById("testFunc").addEventListener("change", updateFuncDisplay);
updateFuncDisplay();

// ── 2D epsilon slider ─────────────────────────────────────────────────────

const epsilonSlider = document.getElementById("slider");
const epsilonInput  = document.getElementById("epsilon");

epsilonSlider.addEventListener("input", () => {
    epsilonInput.value = epsilonSlider.value;
});

epsilonInput.addEventListener("input", () => {
    let val = parseFloat(epsilonInput.value);
    if (!isNaN(val)) epsilonSlider.value = val;
});

epsilonInput.addEventListener("change", () => {
    let val = parseFloat(epsilonInput.value);
    if (!isNaN(val)) {
        epsilonSlider.value = val;
        epsilonInput.value = val.toFixed(1);
    }
});

// ── 2D Go ─────────────────────────────────────────────────────────────────

document.getElementById("Go").addEventListener("click", async () => {
    const rbf     = document.getElementById("RBF").value;
    const epsilon = parseFloat(epsilonSlider.value);
    const errorMsg = document.getElementById("error-msg");
    const plotImg  = document.getElementById("plot-img");

    if (isNaN(epsilon)) {
        errorMsg.textContent = "Please enter a valid epsilon value.";
        return;
    }

    errorMsg.textContent = "Loading...";
    plotImg.style.display = "none";

    try {
        const response = await fetch("/interpolate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rbf, func: document.getElementById("testFunc").value, epsilon })
        });
        const data = await response.json();
        if (data.error) {
            errorMsg.textContent = data.error;
        } else {
            errorMsg.textContent = "";
            plotImg.src = "data:image/png;base64," + data.image;
            plotImg.style.display = "block";
        }
    } catch (err) {
        errorMsg.textContent = "Something went wrong. Is Flask running?";
    }
});

// ── Find Best ε (2D) ──────────────────────────────────────────────────────

document.getElementById("FindBestE").addEventListener("click", async () => {
    const rbf   = document.getElementById("RBF").value;
    const start = parseFloat(document.getElementById("start").value);
    const stop  = parseFloat(document.getElementById("stop").value);

    const msg         = document.getElementById("best-e-msg");
    const interpImg   = document.getElementById("interp-img");
    const cumErrorImg = document.getElementById("cum-error-img");
    const indErrorImg = document.getElementById("ind-error-img");

    if (isNaN(start) || isNaN(stop)) {
        msg.style.color = "#c0392b";
        msg.textContent = "Please enter valid start and stop values.";
        return;
    }

    msg.style.color = "#555";
    msg.textContent = "Searching... (this may take a moment)";
    [interpImg, cumErrorImg, indErrorImg].forEach(img => img.style.display = "none");

    try {
        const response = await fetch("/find_best_e", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rbf, func: document.getElementById("testFunc").value, start, stop })
        });
        const data = await response.json();
        if (data.error) {
            msg.style.color = "#c0392b";
            msg.textContent = data.error;
        } else {
            msg.style.color = "#2c7a2c";
            msg.textContent = `Best ε = ${data.ideal_e}  |  Min cumulative error = ${data.min_error}`;
            interpImg.src   = "data:image/png;base64," + data.interp;
            cumErrorImg.src = "data:image/png;base64," + data.cumulative_error;
            indErrorImg.src = "data:image/png;base64," + data.individual_error;
            [interpImg, cumErrorImg, indErrorImg].forEach(img => img.style.display = "block");
        }
    } catch (err) {
        msg.style.color = "#c0392b";
        msg.textContent = "Something went wrong. Is Flask running?";
    }
});

// ── 3D ε slider ─────────────────────────────────────────────────────

const slider3d = document.getElementById("slider-3d");
const input3d  = document.getElementById("epsilon-3d");

slider3d.addEventListener("input", () => {
    input3d.value = slider3d.value;
});

input3d.addEventListener("input", () => {
    let val = parseFloat(input3d.value);
    if (!isNaN(val)) slider3d.value = val;
});

input3d.addEventListener("change", () => {
    let val = parseFloat(input3d.value);
    if (!isNaN(val)) {
        slider3d.value = val;
        input3d.value = val.toFixed(1);
    }
});

// ── 3D Go ─────────────────────────────────────────────────────────────────

document.getElementById("Go3D").addEventListener("click", async () => {
    const epsilon  = parseFloat(slider3d.value);
    const errorMsg = document.getElementById("error-msg-3d");
    const plotImg  = document.getElementById("plot-img-3d");

    if (isNaN(epsilon)) {
        errorMsg.textContent = "Please enter a valid epsilon value.";
        return;
    }

    errorMsg.textContent = "Loading...";
    plotImg.style.display = "none";

    try {
        const response = await fetch("/interpolate_3d", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rbf: document.getElementById("RBF").value, epsilon })
        });
        const data = await response.json();
        if (data.error) {
            errorMsg.textContent = data.error;
        } else {
            errorMsg.textContent = "";
            plotImg.src = "data:image/png;base64," + data.image;
            plotImg.style.display = "block";
        }
    } catch (err) {
        errorMsg.textContent = "Something went wrong. Is Flask running?";
    }
});

// ── 3D Best ε ─────────────────────────────────────────────────────────────────
document.getElementById("FindBestE3D").addEventListener("click", async () => {
    const msg = document.getElementById("best-e-3d-msg");
    const interpImg   = document.getElementById("interp-img-3d");
    const cumErrorImg = document.getElementById("cum-error-img-3d");
    const indErrorImg = document.getElementById("ind-error-img-3d");

    msg.style.color = "#c0392b";
    msg.textContent = "Unfortunately unavailable.";
    [interpImg, cumErrorImg, indErrorImg].forEach(img => img.style.display = "none");
});