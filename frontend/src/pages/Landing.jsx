import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../AuthContext";

const FEATURES = [
  {
    icon: "🔗",
    title: "Connect any repo",
    desc: "Point RepoChat at a public GitHub repository and we index it in minutes — code, docs, and all.",
  },
  {
    icon: "🧠",
    title: "Ask in plain English",
    desc: "Skip the grep. Ask how something works, where it's implemented, or why a bug might be happening.",
  },
  {
    icon: "📎",
    title: "Answers with sources",
    desc: "Every answer links back to the exact files and chunks it was grounded in, so you can verify it fast.",
  },
  {
    icon: "🕓",
    title: "Full chat history",
    desc: "Every question you've asked, across every repo, saved and searchable so context is never lost.",
  },
];

const STEPS = [
  { n: "01", title: "Add a repository", desc: "Paste a GitHub URL and branch. We clone and process it automatically." },
  { n: "02", title: "We index it", desc: "Your code is chunked, embedded, and made ready for retrieval." },
  { n: "03", title: "Start asking questions", desc: "Chat with your codebase like you would with a teammate who already read it all." },
];

const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    tagline: "Try RepoChat on your own codebase.",
    features: ["1 connected repository", "5 questions total", "Full source citations", "Chat history"],
    cta: "Get started",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$19",
    period: "/ month",
    tagline: "For developers who live in their repos.",
    features: [
      "Unlimited repositories",
      "Unlimited questions",
      "Priority indexing",
      "Full source citations",
      "Chat history",
      "Priority support",
    ],
    cta: "Upgrade to Pro",
    highlight: true,
  },
];

export default function Landing() {
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    const targets = document.querySelectorAll(".reveal");
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            observer.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.15 }
    );
    targets.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <div className="landing">
      <header className="landing-nav">
        <span className="brand">RepoChat</span>
        <nav className="landing-nav-links">
          <a href="#features">Features</a>
          <a href="#pricing">Pricing</a>
        </nav>
        <div className="landing-nav-cta">
          {isAuthenticated ? (
            <Link className="btn-primary" to="/app">
              Go to dashboard
            </Link>
          ) : (
            <>
              <Link className="btn-ghost" to="/login">
                Sign in
              </Link>
              <Link className="btn-primary" to="/register">
                Get started
              </Link>
            </>
          )}
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="hero-badge fade-in">Chat with any GitHub repository</div>
          <h1 className="fade-in delay-1">
            Understand any codebase <span className="accent-text">without reading it line by line</span>
          </h1>
          <p className="hero-sub fade-in delay-2">
            RepoChat indexes your GitHub repository and lets you ask questions in plain English —
            architecture, bugs, "where is this handled" — and get grounded answers with source citations.
          </p>
          <div className="hero-cta fade-in delay-3">
            <Link className="btn-primary btn-lg" to={isAuthenticated ? "/app" : "/register"}>
              {isAuthenticated ? "Go to dashboard" : "Start free — no card required"}
            </Link>
            <a className="btn-secondary btn-lg" href="#pricing">
              See pricing
            </a>
          </div>
          <p className="hero-note fade-in delay-3">Free plan includes 1 repository and 5 questions.</p>
        </section>

        <section className="section" id="features">
          <h2 className="section-title reveal">Everything you need to explore a codebase</h2>
          <p className="section-sub reveal">From first clone to deep architectural questions.</p>
          <div className="feature-grid">
            {FEATURES.map((f, i) => (
              <div className="feature-card reveal" style={{ transitionDelay: `${i * 60}ms` }} key={f.title}>
                <div className="feature-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p className="muted">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="section steps-section">
          <h2 className="section-title reveal">How it works</h2>
          <p className="section-sub reveal">Three steps between a GitHub URL and real answers.</p>
          <div className="steps-grid">
            {STEPS.map((s, i) => (
              <div className="step-card reveal" style={{ transitionDelay: `${i * 80}ms` }} key={s.n}>
                <span className="step-number">{s.n}</span>
                <h3>{s.title}</h3>
                <p className="muted">{s.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="section" id="pricing">
          <h2 className="section-title reveal">Simple, usage-based pricing</h2>
          <p className="section-sub reveal">Start free. Upgrade the moment your repo needs more.</p>
          <div className="pricing-grid">
            {PLANS.map((plan, i) => (
              <div
                className={`pricing-card reveal${plan.highlight ? " pricing-highlight" : ""}`}
                style={{ transitionDelay: `${i * 100}ms` }}
                key={plan.name}
              >
                {plan.highlight && <span className="pricing-tag">Most popular</span>}
                <h3>{plan.name}</h3>
                <p className="muted">{plan.tagline}</p>
                <div className="pricing-price">
                  <span className="pricing-amount">{plan.price}</span>
                  <span className="muted">{plan.period}</span>
                </div>
                <ul className="pricing-features">
                  {plan.features.map((f) => (
                    <li key={f}>
                      <span className="check">✓</span>
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  className={plan.highlight ? "btn-primary" : "btn-secondary"}
                  to={isAuthenticated ? "/app" : "/register"}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </section>

        <section className="section cta-section reveal">
          <h2>Ready to stop grepping?</h2>
          <p className="muted">Connect your first repository in under a minute.</p>
          <Link className="btn-primary btn-lg" to={isAuthenticated ? "/app" : "/register"}>
            {isAuthenticated ? "Go to dashboard" : "Start free"}
          </Link>
        </section>
      </main>

      <footer className="landing-footer">
        <span className="muted small">© {new Date().getFullYear()} RepoChat</span>
      </footer>
    </div>
  );
}
