import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function Layout() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <span className="brand">RepoChat</span>
        <nav className="nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
            Repositories
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => (isActive ? "active" : "")}>
            History
          </NavLink>
        </nav>
        <button className="btn-ghost" onClick={handleLogout}>
          Log out
        </button>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
