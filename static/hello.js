function switchTab(tab) {
    document.getElementById("panel-2d").style.display = tab === "2d" ? "block" : "none";
    document.getElementById("panel-3d").style.display = tab === "3d" ? "block" : "none";
    document.getElementById("panel-best").style.display   = tab === "best"   ? "block" : "none";

    document.querySelectorAll(".tab").forEach((btn, i) => {
        btn.classList.toggle("active", (i === 0 && tab === "2d") || (i === 1 && tab === "3d") || i === 2 && tab === "best");
    });
}

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

const epsilonSlider = document.getElementById("slider");
const epsilonInput  = document.getElementById("epsilon");

epsilonSlider.addEventListener("input", () => {
    epsilonInput.value = epsilonSlider.value;
});

epsilonInput.addEventListener("input", () => {
    // clamp to slider range in case they type something out of bounds
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

document.getElementById("Go").addEventListener("click", async () => {
    const rbf     = document.getElementById("RBF").value;
    const epsilon = parseFloat(epsilonSlider.value);

    const errorMsg = document.getElementById("error-msg");
    const plotImg  = document.getElementById("plot-img");

    // Basic validation
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
            body: JSON.stringify({ epsilon })
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