// ================= CONFIG =================
const API_BASE = "https://personalized-financial-advisory-system-c71w.onrender.com";

// ================= STATE =================
let currentMode = "individual";

// ================= INIT =================
document.addEventListener("DOMContentLoaded", () => {
    setupTabs();
    setupForms();
});

// ================= TAB SWITCH =================
function setupTabs() {
    const individualTab = document.getElementById("tab-individual");
    const orgTab = document.getElementById("tab-organization");

    individualTab?.addEventListener("click", () => switchMode("individual"));
    orgTab?.addEventListener("click", () => switchMode("organization"));
}

function switchMode(mode) {
    currentMode = mode;

    document.getElementById("tab-individual")?.classList.toggle("active", mode === "individual");
    document.getElementById("tab-organization")?.classList.toggle("active", mode === "organization");
}

// ================= FORM SETUP =================
function setupForms() {
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");

    loginForm?.addEventListener("submit", handleLogin);
    signupForm?.addEventListener("submit", handleSignup);
}

// ================= LOGIN =================
async function handleLogin(e) {
    e.preventDefault();

    const identifier = document.getElementById("email")?.value.trim();
    const password = document.getElementById("password")?.value;

    if (!identifier || !password) {
        showAuthError("Enter credentials");
        return;
    }

    try {
        const endpoint =
            currentMode === "organization"
                ? "/org_login"
                : "/login";

        const payload =
            currentMode === "organization"
                ? { org_name: identifier, password }
                : { login_identifier: identifier, password };

        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
            showAuthError(data.error || data.detail || "Login failed");
            return;
        }

        // Save session
        localStorage.setItem("token", data.token);
        localStorage.setItem("userType", currentMode);

        if (currentMode === "organization") {
            localStorage.setItem("userName", data.org_name);
        } else {
            localStorage.setItem("userName", data.name);
            localStorage.setItem("userEmail", data.email);
        }

        redirectToDashboard();

    } catch (err) {
        console.error(err);
        showAuthError("Backend unreachable. Please try again.");
    }
}

// ================= SIGNUP =================
async function handleSignup(e) {
    e.preventDefault();

    const identifier = document.getElementById("email")?.value.trim();
    const password = document.getElementById("password")?.value;

    if (!identifier || !password) {
        showAuthError("Fill all fields");
        return;
    }

    if (password.length < 6) {
        showAuthError("Password must be at least 6 characters");
        return;
    }

    try {
        const endpoint =
            currentMode === "organization"
                ? "/org_signup"
                : "/signup";

        const payload =
            currentMode === "organization"
                ? { org_name: identifier, password }
                : { email: identifier, password };

        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
            showAuthError(data.error || data.detail || "Signup failed");
            return;
        }

        alert("Signup successful. Please login.");

    } catch (err) {
        console.error(err);
        showAuthError("Backend unreachable. Please try again.");
    }
}

// ================= HELPERS =================
function showAuthError(message) {
    const box = document.getElementById("authError");

    if (box) {
        box.innerText = message;
        box.style.display = "block";
    } else {
        alert(message);
    }
}

function redirectToDashboard() {
    window.location.href = "dashboard.html";
}

// ================= LOGOUT =================
function logout() {
    localStorage.clear();
    window.location.href = "index.html";
}
