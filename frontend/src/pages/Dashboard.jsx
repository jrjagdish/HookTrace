import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "../api";

const emptyForm = { name: "", github_url: "", default_branch: "main" };

export default function Dashboard() {
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [creating, setCreating] = useState(false);
  const pollRef = useRef(null);

  async function loadRepos() {
    try {
      const data = await api.getRepositories();
      setRepos(data);
      setError("");
    } catch (err) {
      setError(err.message || "Failed to load repositories");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRepos();
    return () => clearInterval(pollRef.current);
  }, []);

  useEffect(() => {
    const hasProcessing = repos.some((r) => r.status === "processing");
    clearInterval(pollRef.current);
    if (hasProcessing) {
      pollRef.current = setInterval(loadRepos, 4000);
    }
    return () => clearInterval(pollRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repos]);

  async function handleCreate(e) {
    e.preventDefault();
    setCreating(true);
    setError("");
    try {
      await api.createRepository(form);
      setForm(emptyForm);
      await loadRepos();
    } catch (err) {
      setError(err.message || "Failed to add repository");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="page">
      <section className="panel">
        <h2>Add repository</h2>
        <form className="repo-form" onSubmit={handleCreate}>
          <input
            placeholder="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <input
            placeholder="https://github.com/owner/repo"
            value={form.github_url}
            onChange={(e) => setForm({ ...form, github_url: e.target.value })}
            required
          />
          <input
            placeholder="Branch"
            value={form.default_branch}
            onChange={(e) => setForm({ ...form, default_branch: e.target.value })}
            style={{ maxWidth: 120 }}
          />
          <button className="btn-primary" type="submit" disabled={creating}>
            {creating ? "Adding…" : "Add"}
          </button>
        </form>
        {error && <div className="error">{error}</div>}
      </section>

      <section className="panel">
        <h2>Repositories</h2>
        {loading ? (
          <p className="muted">Loading…</p>
        ) : repos.length === 0 ? (
          <p className="muted">No repositories yet. Add one above to get started.</p>
        ) : (
          <ul className="repo-list">
            {repos.map((repo) => (
              <li key={repo.id} className="repo-row">
                <div className="repo-info">
                  <span className="repo-name">{repo.name}</span>
                  <span className="repo-url">{repo.github_url}</span>
                </div>
                <span className={`status status-${repo.status}`}>{repo.status}</span>
                <Link className="btn-secondary" to={`/repositories/${repo.id}`} state={{ name: repo.name }}>
                  Open
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
