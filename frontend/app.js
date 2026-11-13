
// API address: Docker uses the Nginx proxy.
const API_URL = window.location.port === "8080"
    ? "http://127.0.0.1:5000/api"
    : "/api";

// Travel planner elements
const form = document.getElementById("tripForm");
const destinationList = document.getElementById("destinationList");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("error");
const submitBtn = document.getElementById("submitBtn");

// Authentication elements
const authModal = document.getElementById("authModal");
const loginButton = document.getElementById("loginButton");
const signupButton = document.getElementById("signupButton");
const closeAuth = document.getElementById("closeAuth");
const loginTab = document.getElementById("loginTab");
const signupTab = document.getElementById("signupTab");
const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
const authMessage = document.getElementById("authMessage");
const guestButtons = document.getElementById("guestButtons");
const userButtons = document.getElementById("userButtons");
const welcomeUser = document.getElementById("welcomeUser");
const logoutButton = document.getElementById("logoutButton");

// Travel vibe buttons
const vibeButtons = document.querySelectorAll(".vibe");

// ------------------------------
// Authentication functions
// ------------------------------

// Open the authentication popup
function openAuth(mode) {
    authModal.classList.remove("hidden");
    showAuthForm(mode);
}

// Close the popup
function closeAuthModal() {
    authModal.classList.add("hidden");
    authMessage.classList.add("hidden");
}

// Switch between Login and Sign Up
function showAuthForm(mode) {
    authMessage.classList.add("hidden");

    const isLogin = mode === "login";

    loginForm.classList.toggle("hidden", !isLogin);
    signupForm.classList.toggle("hidden", isLogin);

    loginTab.classList.toggle("active", isLogin);
    signupTab.classList.toggle("active", !isLogin);
}

// Display messages inside the popup
function showAuthMessage(message, success = false) {
    authMessage.textContent = message;
    authMessage.classList.remove("hidden", "text-red-300", "text-green-300");

    authMessage.classList.add(
        success ? "text-green-300" : "text-red-300"
    );
}

// Update navigation after login
function updateAuthNavigation(user) {
    guestButtons.classList.add("hidden");
    userButtons.classList.remove("hidden");
    userButtons.classList.add("flex");

    welcomeUser.textContent = `Welcome, ${user.name}`;
}

// Return navigation to guest state
function resetAuthNavigation() {
    guestButtons.classList.remove("hidden");
    userButtons.classList.add("hidden");
    userButtons.classList.remove("flex");

    welcomeUser.textContent = "";
}

// Save login details
function saveLogin(data) {
    localStorage.setItem("tripgenie_token", data.token);
    localStorage.setItem("tripgenie_user", JSON.stringify(data.user));

    updateAuthNavigation(data.user);
}

// Check if a saved login is still valid
async function restoreLogin() {
    const token = localStorage.getItem("tripgenie_token");

    if (!token) {
        resetAuthNavigation();
        return;
    }

    try {
        const response = await fetch(`${API_URL}/me`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const data = await response.json();

        if (!response.ok || !data.user) {
            throw new Error("Login expired");
        }

        localStorage.setItem("tripgenie_user", JSON.stringify(data.user));
        updateAuthNavigation(data.user);

    } catch (error) {
        localStorage.removeItem("tripgenie_token");
        localStorage.removeItem("tripgenie_user");
        resetAuthNavigation();
    }
}

// Open popup buttons
loginButton.addEventListener("click", () => openAuth("login"));
signupButton.addEventListener("click", () => openAuth("signup"));

closeAuth.addEventListener("click", closeAuthModal);

authModal.addEventListener("click", (event) => {
    if (event.target === authModal) {
        closeAuthModal();
    }
});

loginTab.addEventListener("click", () => showAuthForm("login"));
signupTab.addEventListener("click", () => showAuthForm("signup"));

// Registration
signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const button = signupForm.querySelector('button[type="submit"]');
    const originalText = button.textContent;

    const body = {
        name: document.getElementById("signupName").value.trim(),
        email: document.getElementById("signupEmail").value.trim(),
        password: document.getElementById("signupPassword").value
    };

    button.disabled = true;
    button.textContent = "Creating account...";

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Registration failed");
        }

        showAuthMessage(
            "Account created successfully! Please log in.",
            true
        );

        signupForm.reset();

        setTimeout(() => showAuthForm("login"), 1200);

    } catch (error) {
        showAuthMessage(error.message);
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
});

// Login
loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const button = loginForm.querySelector('button[type="submit"]');
    const originalText = button.textContent;

    const body = {
        email: document.getElementById("loginEmail").value.trim(),
        password: document.getElementById("loginPassword").value
    };

    button.disabled = true;
    button.textContent = "Logging in...";

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Login failed");
        }

        saveLogin(data);
        loginForm.reset();
        closeAuthModal();

    } catch (error) {
        showAuthMessage(error.message);
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
});

// Logout
logoutButton.addEventListener("click", () => {
    localStorage.removeItem("tripgenie_token");
    localStorage.removeItem("tripgenie_user");

    resetAuthNavigation();
    alert("You have logged out successfully.");
});

// Restore saved login when the page opens
restoreLogin();

// ------------------------------
// Travel planner functions
// ------------------------------

// Select and deselect travel vibes
vibeButtons.forEach(button => {
    button.addEventListener("click", () => {
        button.classList.toggle("selected");
    });
});

// Submit travel preferences
form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const selectedVibes = Array.from(
        document.querySelectorAll(".vibe.selected")
    ).map(button => button.dataset.vibe);

    if (selectedVibes.length === 0) {
        alert("Please select at least one travel vibe.");
        return;
    }

    const body = {
        budget: document.getElementById("budget").value,
        vibes: selectedVibes,
        travelers: Number(document.getElementById("travelers").value),
        duration: Number(document.getElementById("duration").value)
    };

    loading.classList.remove("hidden");
    errorBox.classList.add("hidden");
    destinationList.innerHTML = "";

    submitBtn.disabled = true;
    submitBtn.textContent = "Finding destinations...";

    try {
        const response = await fetch(`${API_URL}/recommend`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Something went wrong.");
        }

        if (!data.recommendations || data.recommendations.length === 0) {
            throw new Error("No destinations found.");
        }

        displayDestinations(data.recommendations);

        document.getElementById("results").scrollIntoView({
            behavior: "smooth"
        });

    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.classList.remove("hidden");

    } finally {
        loading.classList.add("hidden");
        submitBtn.disabled = false;
        submitBtn.textContent = "✨ Find My Perfect Destination";
    }
});

// Safely display destination cards
function displayDestinations(destinations) {
    destinationList.innerHTML = "";

    destinations.forEach((destination, index) => {
        const card = document.createElement("div");
        card.className = "destination-card";

        const name = document.createElement("h3");
        name.className = "text-2xl font-bold mb-2 gradient-text";
        name.textContent = destination.name || "Unknown destination";

        const country = document.createElement("p");
        country.className = "text-gray-300 mb-4";
        country.textContent = destination.country || "";

        const reason = document.createElement("p");
        reason.className = "text-gray-400 text-sm mb-5";
        reason.textContent = destination.reason ||
            "A destination worth exploring.";

        const cost = document.createElement("p");
        cost.className = "text-purple-300 font-semibold";
        cost.textContent =
            `Estimated daily cost: $${destination.avg_cost_per_day ?? "N/A"}`;

        const score = document.createElement("p");
        score.className = "text-blue-300 text-sm mt-3";
        score.textContent =
            `Match score: ${destination.match_score ?? "N/A"}%`;

        const number = document.createElement("p");
        number.className = "text-gray-500 text-xs mt-4";
        number.textContent = `Recommendation #${index + 1}`;

        card.append(name, country, reason, cost, score, number);
        destinationList.appendChild(card);
    });
}
