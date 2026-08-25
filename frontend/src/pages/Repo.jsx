import { useRef, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import * as api from "../api";

export default function Repo() {
  const { id } = useParams();
  const location = useLocation();
  const repoName = location.state?.name;
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");
  const endRef = useRef(null);

  async function handleAsk(e) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;

    setAsking(true);
    setError("");
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setQuery("");

    try {
      const result = await api.queryRepository(id, q);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: result.answer, sources: result.sources },
      ]);
    } catch (err) {
      setError(err.message || "Query failed");
    } finally {
      setAsking(false);
      setTimeout(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  }

  return (
    <div className="page repo-page">
      <div className="repo-header">
        <Link to="/app" className="back-link">
          ← Repositories
        </Link>
        {repoName && <h2>{repoName}</h2>}
      </div>

      <div className="chat-window">
        {messages.length === 0 && (
          <p className="muted">Ask a question about this repository's codebase.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`bubble bubble-${m.role}`}>
            <p>{m.text}</p>
            {m.sources?.length > 0 && (
              <div className="sources">
                {m.sources.map((s, j) => (
                  <span key={j} className="source-chip">
                    {s.file_path}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {error && <div className="error">{error}</div>}

      <form className="chat-input" onSubmit={handleAsk}>
        <input
          placeholder="Ask about this repository…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={asking}
          autoFocus
        />
        <button className="btn-primary" type="submit" disabled={asking || !query.trim()}>
          {asking ? "Asking…" : "Ask"}
        </button>
      </form>
    </div>
  );
}
