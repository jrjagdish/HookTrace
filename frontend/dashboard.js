requireAuth();

document.getElementById("logout-link").addEventListener("click", logout);

const listEl = document.getElementById("list");
const formEl = document.getElementById("add-repo-form");
const addBtn = document.getElementById("add-repo-btn");
const formError = document.getElementById("form-error");

let pollHandle = null;

function statusBadge(status) {
  const s = (status || "unknown").toLowerCase();
  const label = s === "processing" ? "Processing" : s === "completed" ? "Ready" : s === "failed" ? "Failed" : status;
  return `<span class="badge ${s}"><span class="pulse"></span>${escapeHtml(label)}</span>`;
}

function render(repos) {
  if (!repos || repos.length === 0) {
    listEl.innerHTML = '<div class="empty">No repositories yet. Add one above to start chatting with its code.</div>';
    return;
  }

  listEl.innerHTML = "";
  for (const repo of repos) {
    const card = document.createElement("div");
    card.className = "card repo-card";
    card.dataset.id = repo.id;
    card.innerHTML = `
      <div class="repo-main">
        <div class="repo-name">${escapeHtml(repo.name)}</div>
        <div class="repo-url">${escapeHtml(repo.github_url)} &middot; ${escapeHtml(repo.default_branch)}</div>
      </div>
      <div class="repo-meta">
        ${statusBadge(repo.status)}
        <span style="color:var(--muted);font-size:12px;">${formatDate(repo.created_at)}</span>
      </div>
    `;
    card.addEventListener("click", () => {
      window.location.href = `/repo.html?id=${encodeURIComponent(repo.id)}`;
    });
    listEl.appendChild(card);
  }
}

async function loadRepositories({ silent } = {}) {
  try {
    const repos = await apiFetch("/repositories");
    render(repos);

    const stillProcessing = (repos || []).some(
      (r) => (r.status || "").toLowerCase() === "processing"
    );
    if (stillProcessing && !pollHandle) {
      pollHandle = setInterval(() => loadRepositories({ silent: true }), 5000);
    } else if (!stillProcessing && pollHandle) {
      clearInterval(pollHandle);
      pollHandle = null;
    }
  } catch (err) {
    if (!silent) {
      listEl.innerHTML = `<div class="error-banner">Couldn't load repositories: ${escapeHtml(err.message)}</div>`;
    }
  }
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  formError.style.display = "none";
  addBtn.disabled = true;
  const originalLabel = addBtn.textContent;
  addBtn.innerHTML = '<span class="spinner"></span>';

  const name = document.getElementById("repo-name").value.trim();
  const github_url = document.getElementById("repo-url").value.trim();
  const default_branch = document.getElementById("repo-branch").value.trim() || "main";

  try {
    await apiFetch("/repositories/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, github_url, default_branch }),
    });
    formEl.reset();
    document.getElementById("repo-branch").value = "main";
    await loadRepositories();
  } catch (err) {
    formError.textContent = err.message;
    formError.style.display = "block";
  } finally {
    addBtn.disabled = false;
    addBtn.textContent = originalLabel;
  }
});

loadRepositories();
