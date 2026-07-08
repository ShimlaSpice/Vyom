import { FormEvent, useEffect, useMemo, useState } from 'react';

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

export default function App() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [decisionSymbol, setDecisionSymbol] = useState('RELIANCE');
  const [decisionHorizon, setDecisionHorizon] = useState('intraday');
  const [decisionMessage, setDecisionMessage] = useState<string | null>(null);

  useEffect(() => {
    void loadDashboard();
  }, []);

  const symbolOptions = useMemo(() => dashboard?.symbols ?? [], [dashboard]);

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
    } finally {
      setLoading(false);
    }
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

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">V</div>
          <div>
            <p className="eyebrow">Local Web App</p>
            <h1>VYOM Trader AI</h1>
          </div>
        </div>

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

        {loading ? <section className="panel">Loading dashboard...</section> : null}
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
