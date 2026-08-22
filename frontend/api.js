const TOKEN_KEY = "repochat_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = "/index.html";
  }
}

async function apiFetch(path, options = {}) {
  const headers = options.headers ? { ...options.headers } : {};
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(path, { ...options, headers });
  } catch (networkErr) {
    throw new Error("Can't reach the server. Check your connection and try again.");
  }

  if (response.status === 401) {
    clearToken();
    window.location.href = "/index.html";
    throw new Error("Not authenticated");
  }

  if (!response.ok) {
    let detail = response.statusText || `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body && body.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch (_) {
      // no JSON body
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return null;
  }
  try {
    return await response.json();
  } catch (_) {
    return null;
  }
}

function logout() {
  clearToken();
  window.location.href = "/index.html";
}

function formatDate(iso) {
  if (!iso) return "";
  const withZone = iso.endsWith("Z") ? iso : iso + "Z";
  return new Date(withZone).toLocaleString();
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}
