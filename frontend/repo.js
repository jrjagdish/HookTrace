requireAuth();

document.getElementById("logout-link").addEventListener("click", logout);

const params = new URLSearchParams(window.location.search);
const repoId = params.get("id");
if (!repoId) {
  window.location.href = "/dashboard.html";
}

const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const errorEl = document.getElementById("repo-error");
const processingNotice = document.getElementById("processing-notice");

let hasMessages = false;

function statusBadge(status) {
  const s = (status || "unknown").toLowerCase();
  const label = s === "processing" ? "Processing" : s === "completed" ? "Ready" : s === "failed" ? "Failed" : status;
  return `<span class="badge ${s}"><span class="pulse"></span>${escapeHtml(label)}</span>`;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function clearEmptyState() {
  if (!hasMessages) {
    messagesEl.innerHTML = "";
    hasMessages = true;
  }
}

function appendUserMessage(text) {
  clearEmptyState();
  const div = document.createElement("div");
  div.className = "msg user";
  div.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
  messagesEl.appendChild(div);
  scrollToBottom();
}

function appendTypingIndicator() {
  clearEmptyState();
  const div = document.createElement("div");
  div.className = "msg assistant";
  div.id = "typing-indicator";
  div.innerHTML = `<div class="bubble"><span class="typing-dots"><span></span><span></span><span></span></span></div>`;
  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}

function appendAssistantMessage(answer, sources, isError) {
  const div = document.createElement("div");
  div.className = "msg assistant";
  const sourcesHtml =
    sources && sources.length
      ? `<div class="sources">${sources
          .map((s) => `<span class="source-chip">${escapeHtml(s.file_path)}</span>`)
          .join("")}</div>`
      : "";
  div.innerHTML = `<div class="bubble${isError ? " error" : ""}">${escapeHtml(answer)}</div>${sourcesHtml}`;
  messagesEl.appendChild(div);
  scrollToBottom();
}

async function loadRepoInfo() {
  try {
    const repos = await apiFetch("/repositories");
    const repo = (repos || []).find((r) => r.id === repoId);
    if (!repo) {
      errorEl.textContent = "Repository not found, or you don't have access to it.";
      errorEl.style.display = "block";
      document.getElementById("repo-name").textContent = "Repository not found";
      return;
    }
    document.getElementById("repo-name").textContent = repo.name;
    document.getElementById("repo-url").textContent = `${repo.github_url} · ${repo.default_branch}`;
    document.getElementById("repo-badge").innerHTML = statusBadge(repo.status);
    processingNotice.style.display = (repo.status || "").toLowerCase() === "processing" ? "flex" : "none";
  } catch (err) {
    errorEl.textContent = `Couldn't load repository details: ${err.message}`;
    errorEl.style.display = "block";
  }
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = inputEl.value.trim();
  if (!query) return;

  errorEl.style.display = "none";
  appendUserMessage(query);
  inputEl.value = "";
  inputEl.style.height = "auto";
  sendBtn.disabled = true;
  inputEl.disabled = true;

  const typingEl = appendTypingIndicator();

  try {
    const result = await apiFetch(`/repositories/${encodeURIComponent(repoId)}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: 5 }),
    });
    typingEl.remove();
    appendAssistantMessage(result.answer, result.sources, false);
  } catch (err) {
    typingEl.remove();
    appendAssistantMessage(`Something went wrong answering that: ${err.message}`, [], true);
  } finally {
    sendBtn.disabled = false;
    inputEl.disabled = false;
    inputEl.focus();
  }
});

inputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    formEl.requestSubmit();
  }
});

inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + "px";
});

loadRepoInfo();
