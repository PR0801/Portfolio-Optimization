import { useState, type FormEvent } from 'react';
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  ChevronDown,
  CircleHelp,
  Command,
  Download,
  Gauge,
  Layers3,
  LoaderCircle,
  Menu,
  RefreshCw,
  ShieldAlert,
  SlidersHorizontal,
  Sparkles,
  Target,
  X,
} from 'lucide-react';
import {
  Area,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

type Strategy = 'min_variance' | 'max_sharpe' | 'risk_constrained';
type Recommendation = {
  category: 'strategy' | 'concentration' | 'diversification' | 'downside';
  severity: 'info' | 'caution';
  title: string;
  detail: string;
};

type Analysis = {
  metadata: {
    tickers: string[];
    start: string;
    end: string;
    observations: number;
    strategy: Strategy;
  };
  metrics: {
    annual_return: number;
    annual_volatility: number;
    sharpe_ratio: number;
    daily_var_95: number;
    maximum_drawdown: number;
  };
  weights: { ticker: string; weight: number }[];
  history: {
    date: string;
    portfolio: number;
    benchmark: number;
    rolling_volatility: number | null;
  }[];
  correlation: { tickers: string[]; matrix: number[][] };
  recommendations: Recommendation[];
  disclaimer: string;
  stress: {
    worst_window_return: number;
    worst_drawdown: number;
    stress_regime: boolean;
    window_start: string;
    window_end: string;
  };
};

const today = new Date();
const isoDate = (date: Date) => date.toISOString().slice(0, 10);
const defaultEnd = isoDate(today);
const defaultStartDate = new Date(today);
defaultStartDate.setFullYear(today.getFullYear() - 5);

const strategyOptions: {
  value: Strategy;
  label: string;
  icon: typeof Sparkles;
}[] = [
  { value: 'max_sharpe', label: 'Max Sharpe', icon: Sparkles },
  { value: 'min_variance', label: 'Min variance', icon: ShieldAlert },
  { value: 'risk_constrained', label: 'Risk target', icon: Target },
];

const chartColors = ['#117765', '#e38c66', '#6575a4', '#c7a64a', '#4a9aaa', '#a66879'];

const percent = (value: number, digits = 1) =>
  `${value < 0 ? '−' : ''}${Math.abs(value * 100).toFixed(digits)}%`;

const dateLabel = (date: string) =>
  new Intl.DateTimeFormat('en', { month: 'short', year: '2-digit' }).format(
    new Date(`${date}T00:00:00`),
  );

function App() {
  const [tickers, setTickers] = useState('NVDA, MSFT, GOOGL, AAPL');
  const [start, setStart] = useState(isoDate(defaultStartDate));
  const [end, setEnd] = useState(defaultEnd);
  const [strategy, setStrategy] = useState<Strategy>('max_sharpe');
  const [targetVolatility, setTargetVolatility] = useState(18);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [navNotice, setNavNotice] = useState('');
  const [activeSection, setActiveSection] = useState('overview');
  const [helpOpen, setHelpOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  function navigateTo(section: 'overview' | 'allocation' | 'risk') {
    setActiveSection(section);
    setMobileNavOpen(false);
    setHelpOpen(false);

    if (section !== 'overview' && !analysis) {
      setNavNotice('Run an analysis to unlock allocation and risk views.');
      document.getElementById('analysis-setup')?.scrollIntoView({ behavior: 'smooth' });
      return;
    }

    setNavNotice('');
    document.getElementById(section)?.scrollIntoView({ behavior: 'smooth' });
  }

  async function runAnalysis(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError('');

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tickers: tickers.split(',').map((ticker) => ticker.trim()).filter(Boolean),
          start,
          end,
          strategy,
          risk_free_rate: 0.02,
          target_volatility: strategy === 'risk_constrained' ? targetVolatility / 100 : null,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? 'Analysis could not be completed.');
      setAnalysis(result as Analysis);
      setActiveSection('overview');
      setNavNotice('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to reach the analysis service.');
    } finally {
      setBusy(false);
    }
  }

  const analyzedStrategyName = strategyOptions.find(
    (option) => option.value === analysis?.metadata.strategy,
  )?.label;

  return (
    <div className="app-shell">
      <aside className="rail" aria-label="Primary navigation">
        <a className="brand-mark" href="#top" aria-label="Portfolio Studio home">
          <span className="brand-glyph"><Activity size={20} strokeWidth={2.6} /></span>
        </a>
        <nav className="rail-nav">
          <button type="button" className={activeSection === 'overview' ? 'rail-link active' : 'rail-link'} onClick={() => navigateTo('overview')} aria-label="Portfolio overview" aria-pressed={activeSection === 'overview'} title="Overview">
            <Layers3 size={19} />
          </button>
          <button type="button" className={activeSection === 'allocation' ? 'rail-link active' : 'rail-link'} onClick={() => navigateTo('allocation')} aria-label="Allocation" aria-pressed={activeSection === 'allocation'} title="Allocation">
            <BarChart3 size={19} />
          </button>
          <button type="button" className={activeSection === 'risk' ? 'rail-link active' : 'rail-link'} onClick={() => navigateTo('risk')} aria-label="Risk analysis" aria-pressed={activeSection === 'risk'} title="Risk analysis">
            <Gauge size={19} />
          </button>
        </nav>
        <div className="rail-bottom">
          <button type="button" className="rail-link" aria-label="Help" title="Help" aria-expanded={helpOpen} onClick={() => setHelpOpen(true)}><CircleHelp size={19} /></button>
          <div className="avatar" aria-label="Research workspace">R</div>
        </div>
      </aside>

      <main id="top" className="workspace">
        <header className="topbar">
          <div className="crumbs"><span>Research</span><span className="crumb-slash">/</span><strong>Portfolio studio</strong></div>
          <div className="topbar-right">
            <span className="market-indicator"><i /> Market data via Yahoo Finance</span>
            <button type="button" className="icon-button mobile-menu" aria-label={mobileNavOpen ? 'Close menu' : 'Open menu'} aria-expanded={mobileNavOpen} aria-controls="mobile-navigation" onClick={() => setMobileNavOpen((open) => !open)}>{mobileNavOpen ? <X size={18} /> : <Menu size={18} />}</button>
            <div className="avatar avatar-small">R</div>
          </div>
        </header>
        {mobileNavOpen && (
          <nav className="mobile-nav" id="mobile-navigation" aria-label="Mobile navigation">
            <button type="button" onClick={() => navigateTo('overview')}><Layers3 size={16} />Overview</button>
            <button type="button" onClick={() => navigateTo('allocation')}><BarChart3 size={16} />Allocation</button>
            <button type="button" onClick={() => navigateTo('risk')}><Gauge size={16} />Risk analysis</button>
            <button type="button" onClick={() => { setMobileNavOpen(false); setHelpOpen(true); }}><CircleHelp size={16} />Help</button>
          </nav>
        )}

        <div className="content-wrap">
          <section className="page-heading" id="overview">
            <div>
              <p className="eyebrow">INVESTMENT RESEARCH <span>·</span> WORKSPACE 01</p>
              <h1>Portfolio strategy</h1>
              <p className="heading-copy">Build an allocation, then interrogate its behavior across market history.</p>
            </div>
            <div className="heading-actions">
              <button className="button button-quiet" onClick={() => window.location.reload()}>
                <RefreshCw size={15} /> Reset view
              </button>
              <button className="button button-dark" disabled={!analysis} onClick={() => window.print()}>
                <Download size={15} /> Export report
              </button>
            </div>
          </section>

          <form className="control-panel" id="analysis-setup" onSubmit={runAnalysis}>
            <div className="control-topline">
              <div className="control-label"><SlidersHorizontal size={15} /><span>Analysis setup</span></div>
              <span className="control-hint"><Command size={12} /> Adjust inputs, then run</span>
            </div>
            <div className="control-grid">
              <label className="field ticker-field">
                <span className="field-label">ASSETS <span className="field-note">COMMA SEPARATED</span></span>
                <span className="input-wrap ticker-input-wrap">
                  <input value={tickers} onChange={(event) => setTickers(event.target.value)} aria-label="Asset tickers" required />
                  <ChevronDown size={15} className="input-trailing" />
                </span>
              </label>
              <label className="field">
                <span className="field-label">FROM</span>
                <input className="text-input" type="date" value={start} max={end} onChange={(event) => setStart(event.target.value)} required />
              </label>
              <label className="field">
                <span className="field-label">TO</span>
                <input className="text-input" type="date" value={end} min={start} max={defaultEnd} onChange={(event) => setEnd(event.target.value)} required />
              </label>
              <div className="field strategy-field">
                <span className="field-label">OPTIMIZATION</span>
                <div className="segmented" role="group" aria-label="Optimization strategy">
                  {strategyOptions.map(({ value, label, icon: Icon }) => (
                    <button
                      type="button"
                      key={value}
                      className={strategy === value ? 'segment selected' : 'segment'}
                      onClick={() => setStrategy(value)}
                    >
                      <Icon size={14} /><span>{label}</span>
                    </button>
                  ))}
                </div>
              </div>
              {strategy === 'risk_constrained' && (
                <label className="field target-field">
                  <span className="field-label">ANNUAL VOLATILITY TARGET <strong>{targetVolatility}%</strong></span>
                  <input type="range" min="5" max="40" value={targetVolatility} onChange={(event) => setTargetVolatility(Number(event.target.value))} />
                </label>
              )}
              <button className="button button-run" type="submit" disabled={busy || !tickers.trim()}>
                {busy ? <LoaderCircle className="spin" size={17} /> : <Activity size={17} />}
                {busy ? 'Analyzing history' : 'Run analysis'}
              </button>
            </div>
          </form>

          {error && <div className="error-banner" role="alert"><ShieldAlert size={17} /><span>{error}</span></div>}
          {navNotice && <div className="nav-notice" role="status">{navNotice}</div>}

          {!analysis && !busy && !error ? (
            <section className="welcome-state">
              <div className="welcome-copy">
                <span className="welcome-kicker"><Sparkles size={14} /> RESEARCH, WITHOUT THE SPREADSHEET</span>
                <h2>Start with a question.<br /><em>Leave with a portfolio.</em></h2>
                <p>Choose a universe and optimization objective. The workspace will bring allocation, performance, and downside risk into one view.</p>
                <button className="button button-dark" onClick={() => document.querySelector<HTMLInputElement>('.ticker-input-wrap input')?.focus()}>
                  Set your universe <ArrowUpRight size={15} />
                </button>
              </div>
              <div className="welcome-visual" aria-hidden="true">
                <div className="orbit orbit-one" /><div className="orbit orbit-two" />
                <div className="visual-axis axis-horizontal" /><div className="visual-axis axis-vertical" />
                <div className="visual-dot dot-a" /><div className="visual-dot dot-b" /><div className="visual-dot dot-c" />
                <div className="visual-line" />
                <span className="visual-note note-one">risk</span><span className="visual-note note-two">return</span>
                <span className="visual-equation">σ ↗ &nbsp; μ ↗</span>
              </div>
              <div className="welcome-footer"><span>01 <i /> Define your universe</span><span>02 <i /> Choose a strategy</span><span>03 <i /> Explore the trade-offs</span></div>
            </section>
          ) : (
            <>
              <section className="result-bar" aria-live="polite">
                <div className="result-context">
                  <span className="live-dot" />
                  <strong>{analysis ? 'ANALYSIS COMPLETE' : 'OPTIMIZING PORTFOLIO'}</strong>
                  {analysis && <span className="result-meta">{analysis.metadata.tickers.join(' · ')} <i /> {analysis.metadata.observations} daily observations <i /> {analyzedStrategyName}</span>}
                </div>
                {analysis && <span className="as-of">{dateLabel(analysis.metadata.start)} — {dateLabel(analysis.metadata.end)}</span>}
              </section>

              {analysis && <>
                <section className="metric-grid" aria-label="Portfolio performance metrics">
                  <Metric label="ANNUALIZED RETURN" value={percent(analysis.metrics.annual_return)} tone={analysis.metrics.annual_return >= 0 ? 'positive' : 'negative'} detail="Geometric estimate · daily history" />
                  <Metric label="ANNUALIZED RISK" value={percent(analysis.metrics.annual_volatility)} detail="Standard deviation · 252 days" />
                  <Metric label="SHARPE RATIO" value={analysis.metrics.sharpe_ratio.toFixed(2)} tone="positive" detail="2% risk-free rate" />
                  <Metric label="MAX DRAWDOWN" value={percent(analysis.metrics.maximum_drawdown)} tone="negative" detail={`Daily VaR 95% · ${percent(analysis.metrics.daily_var_95, 2)}`} />
                </section>

                <section className="panel recommendation-panel" aria-labelledby="readout-title">
                  <div className="panel-heading">
                    <div><p className="eyebrow">MODEL INTERPRETATION</p><h2 id="readout-title">Portfolio readout</h2></div>
                    <span className="unit-badge">HISTORICAL · NON-EXECUTABLE</span>
                  </div>
                  <div className="recommendation-grid">
                    {analysis.recommendations.map((recommendation) => (
                      <article className={`recommendation-item ${recommendation.severity}`} key={recommendation.category}>
                        <div className="recommendation-icon">
                          {recommendation.severity === 'caution' ? <ShieldAlert size={16} /> : <Sparkles size={16} />}
                        </div>
                        <div className="recommendation-copy">
                          <div className="recommendation-title"><h3>{recommendation.title}</h3><span>{recommendation.severity === 'caution' ? 'REVIEW' : 'SIGNAL'}</span></div>
                          <p>{recommendation.detail}</p>
                        </div>
                      </article>
                    ))}
                  </div>
                  <p className="recommendation-disclaimer">{analysis.disclaimer}</p>
                </section>

                <section className="analysis-grid">
                  <article className="panel performance-panel">
                    <div className="panel-heading">
                      <div><p className="eyebrow">GROWTH OF 100</p><h2>Portfolio performance</h2></div>
                      <div className="chart-legend"><span><i className="legend-portfolio" /> Portfolio</span><span><i className="legend-benchmark" /> Equal-weight</span></div>
                    </div>
                    <div className="performance-chart">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={analysis.history} margin={{ top: 12, right: 6, bottom: 0, left: -18 }}>
                          <defs><linearGradient id="portfolioFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#117765" stopOpacity={0.17} /><stop offset="100%" stopColor="#117765" stopOpacity={0.01} /></linearGradient></defs>
                          <CartesianGrid vertical={false} stroke="#e9ece7" strokeDasharray="3 5" />
                          <XAxis dataKey="date" tickFormatter={dateLabel} tickLine={false} axisLine={false} minTickGap={42} tick={{ fill: '#7c8782', fontSize: 11 }} />
                          <YAxis tickLine={false} axisLine={false} tick={{ fill: '#7c8782', fontSize: 11 }} domain={['auto', 'auto']} />
                          <Tooltip content={<PerformanceTooltip />} />
                          <Area type="monotone" dataKey="portfolio" stroke="none" fill="url(#portfolioFill)" />
                          <Line type="monotone" dataKey="benchmark" stroke="#d99575" strokeWidth={1.6} dot={false} activeDot={{ r: 4, fill: '#d99575', stroke: '#fff', strokeWidth: 2 }} />
                          <Line type="monotone" dataKey="portfolio" stroke="#117765" strokeWidth={2.5} dot={false} activeDot={{ r: 5, fill: '#117765', stroke: '#fff', strokeWidth: 2 }} />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="chart-footnote"><span>Indexed to 100 at period start</span><span>Past performance does not predict future returns</span></div>
                  </article>

                  <article className="panel allocation-panel" id="allocation">
                    <div className="panel-heading"><div><p className="eyebrow">OPTIMIZED MIX</p><h2>Allocation</h2></div><button className="panel-menu" aria-label="Allocation options"><ChevronDown size={16} /></button></div>
                    <div className="allocation-content">
                      <div className="donut-wrap">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart><Pie data={analysis.weights} dataKey="weight" nameKey="ticker" innerRadius="67%" outerRadius="92%" paddingAngle={3} stroke="none">{analysis.weights.map((entry, index) => <Cell key={entry.ticker} fill={chartColors[index % chartColors.length]} />)}</Pie></PieChart>
                        </ResponsiveContainer>
                        <div className="donut-center"><strong>{analysis.weights.length}</strong><span>ASSETS</span></div>
                      </div>
                      <div className="allocation-list">{analysis.weights.map((asset, index) => <div className="allocation-row" key={asset.ticker}><span className="allocation-name"><i style={{ background: chartColors[index % chartColors.length] }} />{asset.ticker}</span><span className="allocation-value">{percent(asset.weight, 1)}</span></div>)}</div>
                    </div>
                    <div className="allocation-footer"><span>Fully invested</span><strong>{percent(analysis.weights.reduce((sum, asset) => sum + asset.weight, 0), 0)}</strong></div>
                  </article>
                </section>

                <section className="lower-grid" id="risk">
                  <article className="panel risk-panel">
                    <div className="panel-heading"><div><p className="eyebrow">ROLLING WINDOW · 21 DAYS</p><h2>Risk through time</h2></div><span className="unit-badge">ANNUALIZED</span></div>
                    <div className="risk-chart">
                      <ResponsiveContainer width="100%" height="100%"><ComposedChart data={analysis.history} margin={{ top: 8, right: 4, bottom: 0, left: -18 }}>
                        <CartesianGrid vertical={false} stroke="#e9ece7" strokeDasharray="3 5" />
                        <XAxis dataKey="date" tickFormatter={dateLabel} tickLine={false} axisLine={false} minTickGap={42} tick={{ fill: '#7c8782', fontSize: 11 }} />
                        <YAxis tickFormatter={(value) => `${Math.round(value * 100)}%`} tickLine={false} axisLine={false} tick={{ fill: '#7c8782', fontSize: 11 }} />
                        <Tooltip content={<RiskTooltip />} />
                        <Area type="monotone" dataKey="rolling_volatility" stroke="#c7a64a" strokeWidth={2} fill="#c7a64a" fillOpacity={0.12} connectNulls />
                      </ComposedChart></ResponsiveContainer>
                    </div>
                  </article>

                  <article className={analysis.stress.stress_regime ? 'panel stress-panel stress-alert' : 'panel stress-panel'}>
                    <div className="panel-heading"><div><p className="eyebrow">HISTORICAL SCAN</p><h2>Stress regime</h2></div><span className={analysis.stress.stress_regime ? 'stress-status alert' : 'stress-status'}>{analysis.stress.stress_regime ? 'ELEVATED' : 'WITHIN RANGE'}</span></div>
                    <div className="stress-summary"><div className="stress-icon"><Activity size={18} /></div><p>{analysis.stress.stress_regime ? 'A material drawdown appears in the selected history.' : 'No threshold-level stress signal in the selected history.'}</p></div>
                    <div className="stress-values"><div><span>WORST WINDOW</span><strong className={analysis.stress.worst_window_return < 0 ? 'value-negative' : ''}>{percent(analysis.stress.worst_window_return)}</strong></div><div><span>PEAK-TO-TROUGH</span><strong className={analysis.stress.worst_drawdown > 0.1 ? 'value-negative' : ''}>{percent(analysis.stress.worst_drawdown)}</strong></div></div>
                    <p className="stress-date">{analysis.stress.window_start} <ArrowDownRight size={13} /> {analysis.stress.window_end}</p>
                  </article>
                </section>

                <section className="panel correlation-panel">
                  <div className="panel-heading"><div><p className="eyebrow">PAIRWISE RETURNS</p><h2>Correlation matrix</h2></div><span className="unit-badge">−1 TO +1</span></div>
                  <div className="correlation-wrap"><table><thead><tr><th></th>{analysis.correlation.tickers.map((ticker) => <th key={ticker}>{ticker}</th>)}</tr></thead><tbody>{analysis.correlation.tickers.map((ticker, row) => <tr key={ticker}><th>{ticker}</th>{analysis.correlation.matrix[row].map((value, column) => <td key={`${ticker}-${column}`} style={{ background: correlationColor(value) }}>{value.toFixed(2)}</td>)}</tr>)}</tbody></table></div>
                </section>
              </>}
            </>
          )}

          <footer className="page-footer"><span>Portfolio Studio <i /> Quantitative research</span><span>Estimates use historical data and are not investment advice</span></footer>
        </div>
      </main>
      {helpOpen && (
        <div className="help-overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) setHelpOpen(false); }}>
          <section className="help-dialog" role="dialog" aria-modal="true" aria-labelledby="help-title">
            <div className="help-dialog-heading"><div><p className="eyebrow">PORTFOLIO STUDIO</p><h2 id="help-title">About this analysis</h2></div><button type="button" className="icon-button" aria-label="Close help" onClick={() => setHelpOpen(false)}><X size={18} /></button></div>
            <p>Choose assets and a date range, select an optimization objective, then run an analysis to see the estimated allocation and historical risk profile.</p>
            <div className="help-note"><ShieldAlert size={16} /><span>Results are model-based summaries of historical market data, not personalized financial advice. This tool does not place trades or execute orders.</span></div>
            <button type="button" className="button button-dark" onClick={() => { setHelpOpen(false); navigateTo('overview'); }}>Back to analysis</button>
          </section>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, tone, detail }: { label: string; value: string; tone?: 'positive' | 'negative'; detail: string }) {
  return <article className="metric"><div className="metric-top"><span>{label}</span>{tone === 'positive' ? <ArrowUpRight size={15} /> : tone === 'negative' ? <ArrowDownRight size={15} /> : <Activity size={15} />}</div><strong className={tone ? `metric-value ${tone}` : 'metric-value'}>{value}</strong><span className="metric-detail">{detail}</span></article>;
}

function PerformanceTooltip({ active, payload, label }: { active?: boolean; payload?: { dataKey: string; value: number }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return <div className="chart-tooltip"><span>{label}</span>{payload.slice(-2).map((entry) => <div key={entry.dataKey}><i className={entry.dataKey === 'portfolio' ? 'tooltip-green' : 'tooltip-coral'} />{entry.dataKey === 'portfolio' ? 'Portfolio' : 'Equal-weight'} <strong>{entry.value.toFixed(2)}</strong></div>)}</div>;
}

function RiskTooltip({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) {
  if (!active || !payload?.length || payload[0].value == null) return null;
  return <div className="chart-tooltip"><span>{label}</span><div><i className="tooltip-gold" />Rolling volatility <strong>{percent(payload[0].value)}</strong></div></div>;
}

function correlationColor(value: number) {
  const opacity = 0.08 + Math.abs(value) * 0.42;
  return value >= 0 ? `rgba(17, 119, 101, ${opacity})` : `rgba(210, 111, 81, ${opacity})`;
}

export default App;