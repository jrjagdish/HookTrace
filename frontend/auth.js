let mode = "login";

const title = document.getElementById("form-title");
const submitBtn = document.getElementById("submit-btn");
const toggleText = document.getElementById("toggle-text");
const toggleLink = document.getElementById("toggle-link");
const errorEl = document.getElementById("error");
const form = document.getElementById("auth-form");

if (getToken()) {
  window.location.href = "/dashboard.html";
}

toggleLink.addEventListener("click", () => {
  mode = mode === "login" ? "register" : "login";
  errorEl.textContent = "";
  if (mode === "login") {
    title.textContent = "Log in";
    submitBtn.textContent = "Log in";
    toggleText.textContent = "Don't have an account?";
    toggleLink.textContent = "Register";
  } else {
    title.textContent = "Create account";
    submitBtn.textContent = "Register";
    toggleText.textContent = "Already have an account?";
    toggleLink.textContent = "Log in";
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorEl.textContent = "";
  submitBtn.disabled = true;

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  try {
    if (mode === "register") {
      const registerResponse = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!registerResponse.ok) {
        const body = await registerResponse.json().catch(() => ({}));
        throw new Error(body.detail || "Registration failed");
      }
    }

    const loginResponse = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: email, password }),
    });
    if (!loginResponse.ok) {
      const body = await loginResponse.json().catch(() => ({}));
      throw new Error(body.detail || "Incorrect email or password");
    }
    const data = await loginResponse.json();
    setToken(data.access_token);
    window.location.href = "/dashboard.html";
  } catch (err) {
    errorEl.textContent = err.message;
  } finally {
    submitBtn.disabled = false;
  }
});
