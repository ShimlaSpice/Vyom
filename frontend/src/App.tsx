import { FormEvent, useEffect, useMemo, useState } from 'react';

type AuthMode = 'signin' | 'signup';

type SessionUser = {
  name: string;
  email: string;
};

type StoredUser = SessionUser & {
  password: string;
};

type Summary = {
  symbols: number;
  snapshots: number;
  news_items: number;
  decisions: number;
};

type SymbolItem = {
  id: number;
  symbol: string;
  exchange: string;
  instrument_type: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type SnapshotItem = {
  id: number;
  symbol_id: number;
  snapshot_at: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  source: string;
  created_at: string;
  updated_at: string;
};

type NewsItem = {
  id: number;
  symbol_id: number;
  title: string;
  summary: string;
  source: string;
  url: string;
  published_at: string;
  sentiment_score: number;
  created_at: string;
  updated_at: string;
};

type DecisionItem = {
  id: number;
  symbol_id: number;
  symbol: string;
  horizon: string;
  decision: string;
  confidence: number;
  rationale: string;
  model_name: string;
  close_price: number;
  sentiment_score: number;
  created_at: string;
};

type Dashboard = {
  summary: Summary;
  symbols: SymbolItem[];
  latest_snapshots: SnapshotItem[];
  latest_news: NewsItem[];
  latest_decisions: DecisionItem[];
};

const API_BASE_URL = 'http://127.0.0.1:8000';
const AUTH_USERS_KEY = 'vyom_auth_users';
const AUTH_SESSION_KEY = 'vyom_auth_session';

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(value);
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function formatSigned(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}`;
}

function loadStoredUsers(): StoredUser[] {
  if (typeof window === 'undefined') {
    return [];
  }
  const raw = window.localStorage.getItem(AUTH_USERS_KEY);
  if (!raw) {
    return [];
  }
  try {
    return JSON.parse(raw) as StoredUser[];
  } catch {
    return [];
  }
}

function saveStoredUsers(users: StoredUser[]): void {
  window.localStorage.setItem(AUTH_USERS_KEY, JSON.stringify(users));
}

function loadSessionUser(): SessionUser | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const raw = window.localStorage.getItem(AUTH_SESSION_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as SessionUser;
  } catch {
    return null;
  }
}

function saveSessionUser(user: SessionUser): void {
  window.localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(user));
}

function clearSessionUser(): void {
  window.localStorage.removeItem(AUTH_SESSION_KEY);
}

export default function App() {
  const [authMode, setAuthMode] = useState<AuthMode>('signin');
  const [sessionUser, setSessionUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [decisionSymbol, setDecisionSymbol] = useState('RELIANCE');
  const [decisionHorizon, setDecisionHorizon] = useState('intraday');
  const [decisionMessage, setDecisionMessage] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  const symbolOptions = useMemo(() => dashboard?.symbols ?? [], [dashboard]);

  useEffect(() => {
    const storedSession = loadSessionUser();
    if (storedSession) {
      setSessionUser(storedSession);
      void loadDashboard();
    }
    setLoading(false);
  }, []);

  async function loadDashboard() {
    try {
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/dashboard`);
      if (!response.ok) {
        throw new Error(`Dashboard request failed: ${response.status}`);
      }
      const payload = (await response.json()) as Dashboard;
      setDashboard(payload);
      const firstSymbol = payload.symbols[0];
      if (firstSymbol) {
        setDecisionSymbol(firstSymbol.symbol);
      }
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : 'Unable to load dashboard');
    }
  }

  async function handleAuthSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthError(null);

    const form = event.currentTarget;
    const formData = new FormData(form);
    const email = String(formData.get('email') ?? '').trim().toLowerCase();
    const password = String(formData.get('password') ?? '').trim();

    if (!email || !password) {
      setAuthError('Please enter both email and password.');
      return;
    }

    if (authMode === 'signup') {
      const name = String(formData.get('name') ?? '').trim();
      const confirmPassword = String(formData.get('confirm_password') ?? '').trim();
      if (!name) {
        setAuthError('Please enter your full name.');
        return;
      }
      if (password.length < 6) {
        setAuthError('Password must be at least 6 characters.');
        return;
      }
      if (password !== confirmPassword) {
        setAuthError('Passwords do not match.');
        return;
      }
      const users = loadStoredUsers();
      if (users.some((user) => user.email === email)) {
        setAuthError('An account already exists for this email.');
        return;
      }
      const newUser: StoredUser = { name, email, password };
      users.push(newUser);
      saveStoredUsers(users);
      const session = { name, email };
      saveSessionUser(session);
      setSessionUser(session);
      form.reset();
      await loadDashboard();
      return;
    }

    const users = loadStoredUsers();
    const existing = users.find((user) => user.email === email && user.password === password);
    if (!existing) {
      setAuthError('Invalid email or password.');
      return;
    }

    const session = { name: existing.name, email: existing.email };
    saveSessionUser(session);
    setSessionUser(session);
    form.reset();
    await loadDashboard();
  }

  async function handleRunDecision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDecisionMessage(null);
    const response = await fetch(`${API_BASE_URL}/api/decisions/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbol: decisionSymbol, horizon: decisionHorizon }),
    });
    if (!response.ok) {
      setDecisionMessage('Decision engine could not run for that symbol.');
      return;
    }
    const payload = (await response.json()) as DecisionItem;
    setDecisionMessage(
      `${payload.symbol}: ${payload.decision} at ${(payload.confidence * 100).toFixed(0)}% confidence.`,
    );
    await loadDashboard();
  }

  async function handleSeedSymbol(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const symbol = String(formData.get('symbol') ?? '').trim().toUpperCase();
    if (!symbol) {
      return;
    }
    const response = await fetch(`${API_BASE_URL}/api/symbols`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        symbol,
        exchange: String(formData.get('exchange') ?? 'NSE').trim().toUpperCase(),
        instrument_type: String(formData.get('instrument_type') ?? 'EQUITY').trim().toUpperCase(),
        is_active: true,
      }),
    });
    if (!response.ok) {
      setDecisionMessage('Symbol already exists or could not be created.');
      return;
    }
    form.reset();
    await loadDashboard();
  }

  function handleLogout() {
    clearSessionUser();
    setSessionUser(null);
    setDashboard(null);
    setDecisionMessage(null);
    setError(null);
    setAuthMode('signin');
  }

  if (loading) {
    return (
      <div className="app-frame">
        <section className="loading-screen panel">
          <p className="eyebrow">VYOM Trader AI</p>
          <h1>Preparing your workspace</h1>
          <p>Loading the authentication flow and dashboard shell...</p>
        </section>
      </div>
    );
  }

  if (!sessionUser) {
    return (
      <div className="auth-shell">
        <section className="auth-hero">
          <div className="brand">
            <div className="brand-mark">V</div>
            <div>
              <p className="eyebrow">Local Web App</p>
              <h1>VYOM Trader AI</h1>
            </div>
          </div>

          <h2>Sign in to the trading workspace</h2>
          <p>
            A clean local auth screen for your dashboard, with a polished signup and sign-in flow
            that keeps the experience focused and modern.
          </p>

          <div className="auth-features">
            <div>
              <strong>FastAPI</strong>
              <span>Market, news, and decision APIs</span>
            </div>
            <div>
              <strong>SQLite</strong>
              <span>Lightweight local persistence</span>
            </div>
            <div>
              <strong>Alembic</strong>
              <span>Migration-ready schema</span>
            </div>
          </div>
        </section>

        <section className="auth-card panel">
          <div className="auth-tabs">
            <button
              type="button"
              className={authMode === 'signin' ? 'tab active' : 'tab'}
              onClick={() => setAuthMode('signin')}
            >
              Sign in
            </button>
            <button
              type="button"
              className={authMode === 'signup' ? 'tab active' : 'tab'}
              onClick={() => setAuthMode('signup')}
            >
              Sign up
            </button>
          </div>

          <div className="auth-copy">
            <p className="section-label">{authMode === 'signin' ? 'Welcome back' : 'Create account'}</p>
            <h3>{authMode === 'signin' ? 'Sign in to continue' : 'Create your local account'}</h3>
            <p>
              {authMode === 'signin'
                ? 'Use your saved local credentials to open the dashboard.'
                : 'Set up a lightweight local account to access the dashboard.'}
            </p>
          </div>

          <form className="stack auth-form" onSubmit={handleAuthSubmit}>
            {authMode === 'signup' ? (
              <label>
                Full name
                <input name="name" placeholder="Aarav Mehta" autoComplete="name" />
              </label>
            ) : null}
            <label>
              Email
              <input name="email" type="email" placeholder="you@example.com" autoComplete="email" />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                placeholder="••••••••"
                autoComplete={authMode === 'signin' ? 'current-password' : 'new-password'}
              />
            </label>
            {authMode === 'signup' ? (
              <label>
                Confirm password
                <input name="confirm_password" type="password" placeholder="••••••••" autoComplete="new-password" />
              </label>
            ) : null}
            <button type="submit">
              {authMode === 'signin' ? 'Sign in' : 'Create account'}
            </button>
          </form>

          {authError ? <p className="message error-message">{authError}</p> : null}

          <div className="auth-footer">
            <p>
              {authMode === 'signin'
                ? "No account yet? Switch to sign up to create one."
                : 'Already have an account? Switch to sign in.'}
            </p>
            <button
              type="button"
              className="ghost secondary-link"
              onClick={() => setAuthMode(authMode === 'signin' ? 'signup' : 'signin')}
            >
              {authMode === 'signin' ? 'Go to sign up' : 'Go to sign in'}
            </button>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">V</div>
          <div>
            <p className="eyebrow">Signed in as</p>
            <h1>{sessionUser.name}</h1>
          </div>
        </div>

        <section className="panel panel-compact">
          <p className="section-label">Account</p>
          <p className="account-email">{sessionUser.email}</p>
          <button type="button" className="secondary full-width" onClick={handleLogout}>
            Sign out
          </button>
        </section>

        <section className="panel panel-compact">
          <p className="section-label">Quick Stats</p>
          <div className="stats-grid">
            <Stat label="Symbols" value={dashboard?.summary.symbols ?? 0} />
            <Stat label="Snapshots" value={dashboard?.summary.snapshots ?? 0} />
            <Stat label="News" value={dashboard?.summary.news_items ?? 0} />
            <Stat label="Decisions" value={dashboard?.summary.decisions ?? 0} />
          </div>
        </section>

        <section className="panel panel-compact">
          <p className="section-label">Run AI Decision</p>
          <form className="stack" onSubmit={handleRunDecision}>
            <label>
              Symbol
              <select value={decisionSymbol} onChange={(event) => setDecisionSymbol(event.target.value)}>
                {symbolOptions.map((symbol) => (
                  <option key={symbol.id} value={symbol.symbol}>
                    {symbol.symbol}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Horizon
              <select value={decisionHorizon} onChange={(event) => setDecisionHorizon(event.target.value)}>
                <option value="intraday">Intraday</option>
                <option value="swing">Swing</option>
                <option value="positional">Positional</option>
              </select>
            </label>
            <button type="submit">Run decision engine</button>
          </form>
          {decisionMessage ? <p className="message">{decisionMessage}</p> : null}
        </section>

        <section className="panel panel-compact">
          <p className="section-label">Add Symbol</p>
          <form className="stack" onSubmit={handleSeedSymbol}>
            <label>
              Symbol
              <input name="symbol" placeholder="NIFTYBANK" />
            </label>
            <label>
              Exchange
              <input name="exchange" placeholder="NSE" defaultValue="NSE" />
            </label>
            <label>
              Type
              <input name="instrument_type" placeholder="EQUITY" defaultValue="EQUITY" />
            </label>
            <button type="submit" className="secondary">
              Add symbol
            </button>
          </form>
        </section>
      </aside>

      <main className="content">
        <header className="hero">
          <div>
            <p className="eyebrow">FastAPI + React + SQLite + Alembic</p>
            <h2>Market data, news, and explainable decisions in one local dashboard.</h2>
            <p className="hero-copy">
              This web version replaces the desktop shell with a browser-first workflow while
              keeping the AI and market-data boundaries ready for expansion.
            </p>
          </div>
          <button type="button" className="ghost" onClick={() => void loadDashboard()}>
            Refresh
          </button>
        </header>

        {error ? <section className="panel error">Backend unavailable: {error}</section> : null}

        <section className="grid">
          <div className="panel chart-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Symbols</p>
                <h3>Watchlist</h3>
              </div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Exchange</th>
                    <th>Type</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard?.symbols.map((symbol) => (
                    <tr key={symbol.id}>
                      <td>{symbol.symbol}</td>
                      <td>{symbol.exchange}</td>
                      <td>{symbol.instrument_type}</td>
                      <td>{symbol.is_active ? 'Active' : 'Inactive'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel chart-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Signals</p>
                <h3>Latest Decisions</h3>
              </div>
            </div>
            <div className="stack">
              {dashboard?.latest_decisions.map((decision) => (
                <article className="signal-card" key={decision.id}>
                  <div className="signal-top">
                    <strong>{decision.symbol}</strong>
                    <span className={`pill pill-${decision.decision.toLowerCase()}`}>{decision.decision}</span>
                  </div>
                  <p>{decision.rationale}</p>
                  <div className="signal-meta">
                    <span>{decision.horizon}</span>
                    <span>{(decision.confidence * 100).toFixed(0)}% confidence</span>
                    <span>{formatDateTime(decision.created_at)}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="grid">
          <div className="panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Market</p>
                <h3>Recent Snapshots</h3>
              </div>
            </div>
            <div className="stack">
              {dashboard?.latest_snapshots.map((snapshot) => (
                <article className="row-card" key={snapshot.id}>
                  <div>
                    <strong>Symbol #{snapshot.symbol_id}</strong>
                    <p>{formatDateTime(snapshot.snapshot_at)}</p>
                  </div>
                  <div className="metrics">
                    <span>{formatCurrency(snapshot.close_price)}</span>
                    <span>{snapshot.volume.toLocaleString('en-IN')} vol</span>
                    <span>{snapshot.source}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-head">
              <div>
                <p className="section-label">News</p>
                <h3>Recent Headlines</h3>
              </div>
            </div>
            <div className="stack">
              {dashboard?.latest_news.map((item) => (
                <article className="news-card" key={item.id}>
                  <div className="signal-top">
                    <strong>{item.title}</strong>
                    <span className="pill pill-neutral">{formatSigned(item.sentiment_score)}</span>
                  </div>
                  <p>{item.summary}</p>
                  <div className="signal-meta">
                    <span>Symbol #{item.symbol_id}</span>
                    <span>{item.source}</span>
                    <span>{formatDateTime(item.published_at)}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
