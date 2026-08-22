requireAuth();

document.getElementById("logout-link").addEventListener("click", logout);

const listEl = document.getElementById("list");

function render(entries, repoNameById) {
  if (!entries || entries.length === 0) {
    listEl.innerHTML = '<div class="empty">No chat history yet. Ask a repository something to see it here.</div>';
    return;
  }

  const sorted = [...entries].sort(
    (a, b) => new Date(b.created_at) - new Date(a.created_at)
  );

  listEl.innerHTML = "";
  for (const entry of sorted) {
    const repoName = repoNameById.get(entry.repository_id) || "Unknown repository";
    const card = document.createElement("div");
    card.className = "card history-item";
    card.innerHTML = `
      <div class="h-top">
        <span class="h-repo">${escapeHtml(repoName)}</span>
        <span class="h-date">${formatDate(entry.created_at)}</span>
      </div>
      <div class="h-query">${escapeHtml(entry.query)}</div>
      <div class="h-answer">${escapeHtml(entry.answer)}</div>
      <div class="h-actions">
        <button class="danger delete-btn" data-id="${entry.id}">Delete</button>
      </div>
    `;
    listEl.appendChild(card);
  }

  listEl.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", async (event) => {
      event.stopPropagation();
      btn.disabled = true;
      try {
        await apiFetch(`/chat_history/${encodeURIComponent(btn.dataset.id)}`, {
          method: "DELETE",
        });
        await loadHistory();
      } catch (err) {
        btn.disabled = false;
        alert(`Couldn't delete entry: ${err.message}`);
      }
    });
  });
}

async function loadHistory() {
  try {
    const [entries, repos] = await Promise.all([
      apiFetch("/chat_history"),
      apiFetch("/repositories"),
    ]);
    const repoNameById = new Map((repos || []).map((r) => [r.id, r.name]));
    render(entries, repoNameById);
  } catch (err) {
    listEl.innerHTML = `<div class="error-banner">Couldn't load chat history: ${escapeHtml(err.message)}</div>`;
  }
}

loadHistory();
