const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "repochat_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore non-JSON error bodies
    }
    throw new ApiError(
      typeof detail === "string" ? detail : JSON.stringify(detail),
      res.status
    );
  }

  if (res.status === 204) return null;
  return res.json();
}

export function register(email, password) {
  return request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function login(email, password) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const data = await request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  setToken(data.access_token);
  return data;
}

export function getRepositories() {
  return request("/repositories");
}

export function createRepository({ name, github_url, default_branch }) {
  return request("/repositories/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, github_url, default_branch }),
  });
}

export function queryRepository(repositoryId, query, top_k = 5) {
  return request(`/repositories/${repositoryId}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k }),
  });
}

export function getChatHistory() {
  return request("/chat_history");
}

export function deleteChatHistory(chatId) {
  return request(`/chat_history/${chatId}`, { method: "DELETE" });
}

export { ApiError };
