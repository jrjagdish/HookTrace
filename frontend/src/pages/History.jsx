import { useEffect, useState } from "react";
import * as api from "../api";

export default function History() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getChatHistory()
      .then(setEntries)
      .catch((err) => setError(err.message || "Failed to load history"))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(chatId) {
    try {
      await api.deleteChatHistory(chatId);
      setEntries((prev) => prev.filter((e) => e.id !== chatId));
    } catch (err) {
      setError(err.message || "Failed to delete entry");
    }
  }

  return (
    <div className="page">
      <section className="panel">
        <h2>Chat history</h2>
        {error && <div className="error">{error}</div>}
        {loading ? (
          <p className="muted">Loading…</p>
        ) : entries.length === 0 ? (
          <p className="muted">No queries yet.</p>
        ) : (
          <ul className="history-list">
            {entries.map((entry) => (
              <li key={entry.id} className="history-item">
                <div className="history-content">
                  <p className="history-query">{entry.query}</p>
                  <p className="history-answer">{entry.answer}</p>
                  <span className="history-date">
                    {new Date(entry.created_at).toLocaleString()}
                  </span>
                </div>
                <button className="btn-ghost" onClick={() => handleDelete(entry.id)}>
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
