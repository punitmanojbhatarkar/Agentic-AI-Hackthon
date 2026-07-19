import React, { useState, useEffect, useRef, useCallback } from 'react';

// ============================================================================
// CONFIG & UTILITIES
// ============================================================================

const API_BASE = 'http://localhost:5000/api';

const getRiskColor = (level) => {
  switch (level?.toLowerCase()) {
    case 'critical': return '#dc2626';
    case 'high':     return '#ea580c';
    case 'medium':   return '#ca8a04';
    case 'low':      return '#16a34a';
    default:         return '#6b7280';
  }
};

const getRiskBg = (level) => {
  switch (level?.toLowerCase()) {
    case 'critical': return 'rgba(220,38,38,0.15)';
    case 'high':     return 'rgba(234,88,12,0.15)';
    case 'medium':   return 'rgba(202,138,4,0.15)';
    case 'low':      return 'rgba(22,163,74,0.15)';
    default:         return 'rgba(107,114,128,0.15)';
  }
};

const getStatusColor = (status) => {
  switch (status) {
    case 'approved':         return '#16a34a';
    case 'rejected':         return '#dc2626';
    case 'pending_approval': return '#ca8a04';
    case 'executed':         return '#2563eb';
    default:                 return '#6b7280';
  }
};

const fmt = (n, decimals = 1) => {
  if (n === null || n === undefined) return '—';
  return typeof n === 'number' ? (Number.isInteger(n) ? n.toString() : n.toFixed(decimals)) : String(n);
};

const fmtDate = (s) => s ? new Date(s).toLocaleString() : '—';

const api = async (path, opts = {}) => {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`);
  return json;
};

// ============================================================================
// SHARED COMPONENTS
// ============================================================================

const Spinner = ({ size = 20 }) => (
  <div style={{
    width: size, height: size, border: '2px solid rgba(255,255,255,0.2)',
    borderTop: '2px solid #f97316', borderRadius: '50%',
    animation: 'spin 0.8s linear infinite', display: 'inline-block'
  }} />
);

const Toast = ({ msg, type = 'success', onDone }) => {
  useEffect(() => { const t = setTimeout(onDone, 2800); return () => clearTimeout(t); }, [onDone]);
  const colors = { success: '#16a34a', error: '#dc2626', info: '#2563eb' };
  return (
    <div style={{
      position: 'fixed', bottom: 24, right: 24, zIndex: 9999,
      background: colors[type] || colors.info, color: '#fff',
      padding: '12px 20px', borderRadius: 10, fontWeight: 600,
      boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
      animation: 'slideUp 0.3s ease-out'
    }}>{msg}</div>
  );
};

const Badge = ({ label, color }) => (
  <span style={{
    background: color, color: '#fff', padding: '2px 10px',
    borderRadius: 999, fontSize: 11, fontWeight: 700,
    letterSpacing: '0.05em', whiteSpace: 'nowrap'
  }}>{label}</span>
);

const Modal = ({ title, onClose, children, width = 480 }) => (
  <div style={{
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
  }} onClick={e => e.target === e.currentTarget && onClose()}>
    <div style={{
      background: '#1e2330', border: '1px solid #374151', borderRadius: 14,
      padding: 28, width, maxWidth: '95vw', maxHeight: '90vh', overflowY: 'auto',
      boxShadow: '0 20px 60px rgba(0,0,0,0.5)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ margin: 0, color: '#f1f5f9', fontSize: 18, fontWeight: 700 }}>{title}</h3>
        <button onClick={onClose} style={{
          background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: 22, lineHeight: 1
        }}>×</button>
      </div>
      {children}
    </div>
  </div>
);

const FormField = ({ label, value, onChange, type = 'text', placeholder = '', required = false }) => (
  <div style={{ marginBottom: 14 }}>
    <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 5 }}>
      {label}{required && <span style={{ color: '#f97316' }}> *</span>}
    </label>
    <input
      type={type} value={value} onChange={e => onChange(e.target.value)}
      placeholder={placeholder} required={required}
      style={{
        width: '100%', background: '#111827', border: '1px solid #374151',
        borderRadius: 8, color: '#f1f5f9', padding: '9px 12px', fontSize: 14,
        outline: 'none', boxSizing: 'border-box'
      }}
    />
  </div>
);

const Btn = ({ children, onClick, variant = 'primary', loading = false, small = false, disabled = false }) => {
  const styles = {
    primary:  { background: '#f97316', color: '#fff' },
    danger:   { background: '#dc2626', color: '#fff' },
    ghost:    { background: 'transparent', color: '#9ca3af', border: '1px solid #374151' },
    success:  { background: '#16a34a', color: '#fff' },
  };
  return (
    <button onClick={onClick} disabled={loading || disabled} style={{
      ...styles[variant], border: 'none', borderRadius: 8,
      padding: small ? '6px 12px' : '9px 18px',
      fontSize: small ? 12 : 14, fontWeight: 600, cursor: 'pointer',
      display: 'inline-flex', alignItems: 'center', gap: 6,
      opacity: (loading || disabled) ? 0.6 : 1, transition: 'opacity 0.2s'
    }}>
      {loading && <Spinner size={14} />}
      {children}
    </button>
  );
};

const EmptyState = ({ icon, text }) => (
  <div style={{ textAlign: 'center', padding: '48px 24px', color: '#6b7280' }}>
    <div style={{ fontSize: 40, marginBottom: 12 }}>{icon}</div>
    <p style={{ margin: 0, fontSize: 14 }}>{text}</p>
  </div>
);

// ============================================================================
// SIDEBAR NAVIGATION
// ============================================================================

const NAV_ITEMS = [
  { id: 'dashboard',  label: 'Dashboard',   icon: '📊' },
  { id: 'inventory',  label: 'Inventory',   icon: '📦' },
  { id: 'suppliers',  label: 'Suppliers',   icon: '🏭' },
  { id: 'history',    label: 'Action History', icon: '📋' },
];

const Sidebar = ({ active, onNav }) => (
  <aside style={{
    width: 220, background: '#111827', borderRight: '1px solid #1f2937',
    display: 'flex', flexDirection: 'column', flexShrink: 0,
    height: '100vh', position: 'sticky', top: 0
  }}>
    <div style={{ padding: '28px 20px 20px' }}>
      <div style={{ fontSize: 22, fontWeight: 800, color: '#f97316', letterSpacing: '-0.5px' }}>
        Supply<span style={{ color: '#f1f5f9' }}>Sense</span>
      </div>
      <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>AI Supply Chain Intelligence</div>
    </div>
    <nav style={{ flex: 1, padding: '0 10px' }}>
      {NAV_ITEMS.map(item => (
        <button key={item.id} onClick={() => onNav(item.id)} style={{
          display: 'flex', alignItems: 'center', gap: 12, width: '100%',
          padding: '11px 14px', marginBottom: 4, border: 'none', borderRadius: 10,
          background: active === item.id ? 'rgba(249,115,22,0.15)' : 'transparent',
          color: active === item.id ? '#f97316' : '#9ca3af',
          fontSize: 14, fontWeight: active === item.id ? 700 : 500,
          cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s'
        }}>
          <span style={{ fontSize: 18 }}>{item.icon}</span>
          {item.label}
          {active === item.id && (
            <div style={{ marginLeft: 'auto', width: 4, height: 4, borderRadius: '50%', background: '#f97316' }} />
          )}
        </button>
      ))}
    </nav>
    <div style={{ padding: '16px 20px', borderTop: '1px solid #1f2937', fontSize: 11, color: '#4b5563' }}>
      SupplySense v1.0 — Hackathon
    </div>
  </aside>
);

// ============================================================================
// PAGE: DASHBOARD
// ============================================================================

const SkeletonRow = () => (
  <div style={{ height: 60, background: 'rgba(255,255,255,0.04)', borderRadius: 8, marginBottom: 8, animation: 'pulse 1.5s infinite' }} />
);

const StatCard = ({ icon, label, value, sub, color = '#f97316' }) => (
  <div style={{
    background: '#1e2330', border: '1px solid #1f2937', borderRadius: 12,
    padding: '18px 20px', display: 'flex', alignItems: 'center', gap: 16
  }}>
    <div style={{ fontSize: 32 }}>{icon}</div>
    <div>
      <div style={{ fontSize: 26, fontWeight: 800, color }}>{value}</div>
      <div style={{ fontSize: 13, color: '#9ca3af', fontWeight: 600 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>{sub}</div>}
    </div>
  </div>
);

const AgentResponse = ({ response }) => {
  const [show, setShow] = useState(false);
  if (!response) return null;
  const confColor = response.confidence === 'high' ? '#16a34a' : response.confidence === 'medium' ? '#ca8a04' : '#dc2626';
  return (
    <div style={{ background: '#1e3a5f', border: '1px solid #1d4ed8', borderRadius: 12, padding: 16, maxWidth: 520 }}>
      <p style={{ margin: '0 0 10px', color: '#bfdbfe', fontSize: 14, lineHeight: 1.55 }}>{response.final_answer}</p>
      {response.execution_trace?.length > 0 && (
        <button onClick={() => setShow(s => !s)} style={{
          background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer',
          fontSize: 12, fontWeight: 600, padding: 0, marginBottom: show ? 8 : 0
        }}>{show ? '▼ Hide reasoning' : '▶ Show reasoning'}</button>
      )}
      {show && (
        <div style={{ borderLeft: '2px solid #f97316', paddingLeft: 12, marginTop: 8 }}>
          {response.execution_trace.map((s, i) => (
            <div key={i} style={{ fontSize: 12, color: '#93c5fd', marginBottom: 4 }}>
              <strong>Step {s.step}:</strong> {s.tool} — {s.reasoning}
              {s.error && <span style={{ color: '#fca5a5' }}> ✗ {s.error}</span>}
            </div>
          ))}
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 10, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: confColor }} />
        <span style={{ fontSize: 11, color: '#60a5fa' }}>{response.confidence} confidence</span>
        {response.caveats && <span style={{ fontSize: 11, color: '#6b7280', marginLeft: 8, fontStyle: 'italic' }}>· {response.caveats}</span>}
      </div>
    </div>
  );
};

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const send = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const q = input.trim();
    setInput('');
    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', content: q }]);
    try {
      const data = await api('/query', { method: 'POST', body: JSON.stringify({ question: q }) });
      setMessages(prev => [...prev, { role: 'agent', content: data }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'error', content: err.message }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background: '#1e2330', border: '1px solid #1f2937', borderRadius: 14, display: 'flex', flexDirection: 'column', height: 420 }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid #1f2937', fontWeight: 700, color: '#f1f5f9', fontSize: 16 }}>
        💬 Ask SupplySense
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#6b7280', fontSize: 13, padding: '20px 0' }}>
            Ask anything about inventory, disruptions, or supplier risks…
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            {m.role === 'user' ? (
              <div style={{ background: '#ea580c', color: '#fff', borderRadius: 12, padding: '10px 16px', maxWidth: 360, fontSize: 14 }}>{m.content}</div>
            ) : m.role === 'error' ? (
              <div style={{ background: '#7f1d1d', color: '#fca5a5', borderRadius: 12, padding: '10px 16px', fontSize: 14 }}>{m.content}</div>
            ) : (
              <AgentResponse response={m.content} />
            )}
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ background: '#374151', color: '#d1d5db', borderRadius: 12, padding: '10px 16px', fontSize: 14, display: 'flex', gap: 8, alignItems: 'center' }}>
              <Spinner size={14} /> SupplySense is thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={send} style={{ padding: 16, borderTop: '1px solid #1f2937', display: 'flex', gap: 10 }}>
        <input value={input} onChange={e => setInput(e.target.value)} disabled={loading}
          placeholder="What is causing today's biggest disruption?"
          style={{
            flex: 1, background: '#111827', border: '1px solid #374151', borderRadius: 8,
            color: '#f1f5f9', padding: '10px 14px', fontSize: 14, outline: 'none'
          }}
        />
        <Btn disabled={!input.trim()} loading={loading}>Send</Btn>
      </form>
    </div>
  );
};

const DashboardPage = () => {
  const [sweep, setSweep] = useState(null);
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actLoading, setActLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [expandedSup, setExpandedSup] = useState(null);

  // New panel data
  const [shipmentDelays, setShipmentDelays] = useState([]);
  const [warehouseUtil, setWarehouseUtil] = useState([]);
  const [demandForecast, setDemandForecast] = useState([]);
  const [panelLoading, setPanelLoading] = useState(true);

  const fetchSweep = useCallback(async () => {
    setLoading(true);
    try { setSweep(await api('/sweep')); }
    catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  const fetchActions = useCallback(async () => {
    setActLoading(true);
    try { setActions(await api('/pending-actions')); }
    catch (e) { console.error(e); }
    finally { setActLoading(false); }
  }, []);

  const fetchPanels = useCallback(async () => {
    setPanelLoading(true);
    try {
      const [delays, util, forecast] = await Promise.all([
        api('/shipment-delays'),
        api('/warehouse-utilization'),
        api('/demand-forecast'),
      ]);
      setShipmentDelays(delays);
      setWarehouseUtil(util);
      setDemandForecast(forecast);
    } catch (e) { console.error('Panel fetch error:', e); }
    finally { setPanelLoading(false); }
  }, []);

  useEffect(() => { fetchSweep(); fetchActions(); fetchPanels(); }, [fetchSweep, fetchActions, fetchPanels]);

  const handleAction = async (id, status) => {
    try {
      await api(`/pending-actions/${id}/status`, { method: 'POST', body: JSON.stringify({ status }) });
      setActions(prev => prev.filter(a => a.action_id !== id));
      setToast({ msg: status === 'approved' ? '✓ Action approved' : '✗ Action rejected', type: status === 'approved' ? 'success' : 'error' });
    } catch (e) { setToast({ msg: e.message, type: 'error' }); }
  };

  const stats = sweep?.scan_stats || {};

  return (
    <div>
      {toast && <Toast msg={toast.msg} type={toast.type} onDone={() => setToast(null)} />}

      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 800, color: '#f1f5f9' }}>Operations Dashboard</h1>
        <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: 14 }}>
          {sweep?.timestamp ? `Last sweep: ${fmtDate(sweep.timestamp)}` : 'Loading…'}
        </p>
      </div>

      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 28 }}>
        <StatCard icon="🔴" label="Critical Stockouts" value={stats.critical_count ?? '—'} color="#dc2626" />
        <StatCard icon="🟠" label="High Risk SKUs" value={stats.high_count ?? '—'} color="#ea580c" />
        <StatCard icon="⚠️" label="Risky Suppliers" value={stats.risky_supplier_count ?? '—'} color="#ca8a04" />
        <StatCard icon="🤖" label="Pending Actions" value={actions.length} color="#f97316" />
      </div>

      {/* Executive Summary */}
      <div style={{
        background: 'linear-gradient(135deg, #1e3a5f, #1e2330)', border: '1px solid #1d4ed8',
        borderLeft: '4px solid #f97316', borderRadius: 14, padding: '20px 24px', marginBottom: 28
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#f1f5f9' }}>🧠 Executive Summary</h2>
          <Btn onClick={fetchSweep} loading={loading} small>{loading ? 'Analyzing…' : '↻ Refresh'}</Btn>
        </div>
        {loading ? (
          <div style={{ color: '#60a5fa', fontSize: 14 }}>⏳ Running intelligence sweep…</div>
        ) : sweep?.executive_summary ? (
          <p style={{ margin: 0, color: '#bfdbfe', fontSize: 14, lineHeight: 1.65, whiteSpace: 'pre-line' }}>
            {sweep.executive_summary}
          </p>
        ) : (
          <p style={{ margin: 0, color: '#6b7280' }}>No analysis available yet. Click Refresh.</p>
        )}
      </div>

      {/* Three panels */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20, marginBottom: 28 }}>

        {/* Critical Shortages */}
        <div style={{ background: '#1e2330', border: '1px solid #1f2937', borderRadius: 14, padding: 20 }}>
          <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 16, fontWeight: 700 }}>📦 Inventory Shortages</h3>
          {loading ? [1,2,3].map(i => <SkeletonRow key={i} />) :
            sweep?.critical_stockouts?.length > 0 ? (
              <div style={{ maxHeight: 380, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[...(sweep.critical_stockouts)].sort((a,b) => {
                  const o = { critical:0, high:1, medium:2 };
                  return (o[a.risk_level]??9) - (o[b.risk_level]??9);
                }).map((s, i) => (
                  <div key={i} style={{
                    background: getRiskBg(s.risk_level), border: `1px solid ${getRiskColor(s.risk_level)}44`,
                    borderLeft: `4px solid ${getRiskColor(s.risk_level)}`, borderRadius: 10, padding: 14
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, flexWrap: 'wrap', gap: 4 }}>
                      <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 14 }}>{s.sku_id}</span>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {s.demand_spike_detected && <Badge label="⚡ DEMAND SPIKE" color="#7c3aed" />}
                        {s.overstock_risk && <Badge label="📈 OVERSTOCK" color="#0e7490" />}
                        <Badge label={s.risk_level?.toUpperCase()} color={getRiskColor(s.risk_level)} />
                      </div>
                    </div>
                    <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 6 }}>@ {s.warehouse_id}</div>
                    <div style={{ fontSize: 22, fontWeight: 800, color: '#fb923c' }}>{fmt(s.days_until_stockout)}</div>
                    <div style={{ fontSize: 11, color: '#6b7280' }}>days until stockout</div>
                    {s.overstock_ratio != null && (
                      <div style={{ fontSize: 11, color: '#0e7490', marginTop: 3 }}>
                        Stock = {fmt(s.overstock_ratio, 1)}x weekly demand
                      </div>
                    )}
                    <div style={{ marginTop: 8, fontSize: 12, color: '#d1d5db', background: 'rgba(0,0,0,0.2)', borderRadius: 6, padding: '6px 10px' }}>
                      Reorder: <strong>{fmt(s.recommended_reorder_quantity, 0)}</strong> units
                    </div>
                  </div>
                ))}
              </div>
            ) : <EmptyState icon="✅" text="No critical shortages detected" />
          }
        </div>

        {/* Supplier Risk */}
        <div style={{ background: '#1e2330', border: '1px solid #1f2937', borderRadius: 14, padding: 20 }}>
          <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 16, fontWeight: 700 }}>⚠️ Supplier Risk</h3>
          {loading ? [1,2].map(i => <SkeletonRow key={i} />) :
            sweep?.risky_suppliers?.length > 0 ? (
              <div style={{ maxHeight: 380, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {sweep.risky_suppliers.map((s, i) => (
                  <div key={i} style={{
                    background: getRiskBg(s.risk_category), border: `1px solid ${getRiskColor(s.risk_category)}44`,
                    borderLeft: `4px solid ${getRiskColor(s.risk_category)}`, borderRadius: 10,
                    padding: 14, cursor: 'pointer'
                  }} onClick={() => setExpandedSup(expandedSup === i ? null : i)}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 14 }}>{s.supplier_id}</span>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span style={{ fontSize: 13, color: '#9ca3af' }}>Score: {fmt(s.score)}</span>
                        <Badge label={s.risk_category?.toUpperCase()} color={getRiskColor(s.risk_category)} />
                      </div>
                    </div>
                    {expandedSup === i && s.breakdown && (
                      <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {[
                          ['On-time delivery', `${fmt(s.breakdown.on_time_delivery_pct)}%`],
                          ['Lead time variance', `${fmt(s.breakdown.lead_time_variance_days)} days`],
                          ['Quality score', `${fmt(s.breakdown.avg_quality_score)}/100`],
                        ].map(([k, v]) => (
                          <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                            <span style={{ color: '#6b7280' }}>{k}</span>
                            <span style={{ color: '#d1d5db', fontWeight: 600 }}>{v}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : <EmptyState icon="✅" text="No high-risk suppliers detected" />
          }
        </div>

        {/* Pending Actions */}
        <div style={{ background: '#1e2330', border: '1px solid #1f2937', borderRadius: 14, padding: 20 }}>
          <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 16, fontWeight: 700 }}>🤖 Agent Actions</h3>
          {actLoading ? [1,2].map(i => <SkeletonRow key={i} />) :
            actions.length > 0 ? (
              <div style={{ maxHeight: 380, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {actions.map((a, i) => (
                  <div key={i} style={{ background: 'rgba(37,99,235,0.1)', border: '1px solid rgba(37,99,235,0.3)', borderLeft: '4px solid #2563eb', borderRadius: 10, padding: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 13 }}>
                        {a.action_type === 'reorder' ? '📦 Reorder Stock' : '🔄 Switch Supplier'}
                      </span>
                      <Badge label={a.status?.replace(/_/g,' ').toUpperCase()} color={getStatusColor(a.status)} />
                    </div>
                    <div style={{ fontSize: 12, color: '#9ca3af', background: 'rgba(0,0,0,0.2)', borderRadius: 6, padding: '6px 10px', marginBottom: 8 }}>
                      {Object.entries(a.details || {}).map(([k, v]) => (
                        <div key={k}><span style={{ color: '#6b7280' }}>{k}:</span> {String(v)}</div>
                      ))}
                    </div>
                    {a.reasoning && <p style={{ margin: '0 0 10px', fontSize: 12, color: '#9ca3af', fontStyle: 'italic' }}>{a.reasoning}</p>}
                    {a.status === 'pending_approval' && (
                      <div style={{ display: 'flex', gap: 8 }}>
                        <Btn variant="success" small onClick={() => handleAction(a.action_id, 'approved')}>✓ Approve</Btn>
                        <Btn variant="danger" small onClick={() => handleAction(a.action_id, 'rejected')}>✗ Reject</Btn>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : <EmptyState icon="✅" text="No pending actions" />
          }
        </div>
      </div>

      {/* ── Second row: 3 new panels ─────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20, marginBottom: 28 }}>

        {/* Shipment Delays */}
        <div style={{ background: '#1e2330', border: '1px solid #1f2937', borderRadius: 14, padding: 20 }}>
          <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 16, fontWeight: 700 }}>🚛 Shipment Delays</h3>
          {panelLoading ? [1,2].map(i => <SkeletonRow key={i} />) :
            shipmentDelays.length > 0 ? (
              <div style={{ maxHeight: 340, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {shipmentDelays.slice(0,10).map((sh, i) => (
                  <div key={i} style={{
                    background: getRiskBg(sh.severity), border: `1px solid ${getRiskColor(sh.severity)}44`,
                    borderLeft: `4px solid ${getRiskColor(sh.severity)}`, borderRadius: 10, padding: 12
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 13 }}>{sh.shipment_id}</span>
                      <Badge label={sh.severity?.toUpperCase()} color={getRiskColor(sh.severity)} />
                    </div>
                    <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>
                      Status: <span style={{ color: '#d1d5db', fontWeight: 600 }}>{sh.current_status}</span>
                    </div>
                    <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>
                      Promised: {sh.promised_date} · Est: {sh.estimated_delivery || '—'}
                    </div>
                    <div style={{ fontSize: 20, fontWeight: 800, color: '#f87171' }}>{sh.delay_days} days late</div>
                  </div>
                ))}
              </div>
            ) : <EmptyState icon="✅" text="No active delays detected" />
          }
        </div>

        {/* Warehouse Utilization */}
        <div style={{ background: '#1e2330', border: '1px solid #1f2937', borderRadius: 14, padding: 20 }}>
          <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 16, fontWeight: 700 }}>🏭 Warehouse Utilization</h3>
          {panelLoading ? [1,2].map(i => <SkeletonRow key={i} />) :
            warehouseUtil.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {warehouseUtil.map((w, i) => {
                  const pct = w.utilization_pct;
                  const barColor = pct >= 90 ? '#dc2626' : pct >= 70 ? '#ca8a04' : '#16a34a';
                  return (
                    <div key={i}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, alignItems: 'baseline' }}>
                        <div>
                          <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 13 }}>{w.warehouse_id}</span>
                          <span style={{ color: '#6b7280', fontSize: 11, marginLeft: 6 }}>{w.name}</span>
                        </div>
                        <span style={{ fontWeight: 800, color: barColor, fontSize: 15 }}>{pct}%</span>
                      </div>
                      {/* Progress bar */}
                      <div style={{ background: '#111827', borderRadius: 999, height: 8, overflow: 'hidden' }}>
                        <div style={{
                          width: `${Math.min(pct, 100)}%`, height: '100%',
                          background: barColor, borderRadius: 999,
                          transition: 'width 0.6s ease'
                        }} />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 3, fontSize: 11, color: '#6b7280' }}>
                        <span>{w.total_stock?.toLocaleString()} units stored</span>
                        <span>cap: {w.capacity?.toLocaleString()}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : <EmptyState icon="🏭" text="No warehouse data" />
          }
        </div>

        {/* Demand Forecast */}
        <div style={{ background: '#1e2330', border: '1px solid #1f2937', borderRadius: 14, padding: 20 }}>
          <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 16, fontWeight: 700 }}>📈 7-Day Demand Forecast</h3>
          <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 12 }}>Top 5 highest-risk SKUs by days of stock remaining</div>
          {panelLoading ? [1,2,3].map(i => <SkeletonRow key={i} />) :
            demandForecast.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {demandForecast.map((fc, i) => {
                  const maxD = Math.max(...(fc.forecasted_daily_demand || [1]));
                  const trendIcon = fc.trend === 'increasing' ? '↑' : fc.trend === 'decreasing' ? '↓' : '→';
                  const trendColor = fc.trend === 'increasing' ? '#f87171' : fc.trend === 'decreasing' ? '#4ade80' : '#9ca3af';
                  return (
                    <div key={i} style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 10, padding: '12px 14px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                          <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 13 }}>{fc.sku_id}</span>
                          <span style={{ color: trendColor, fontSize: 13, fontWeight: 700 }}>{trendIcon}</span>
                          {fc.demand_spike_detected && <Badge label="⚡ SPIKE" color="#7c3aed" />}
                        </div>
                        <span style={{ fontSize: 11, color: '#6b7280' }}>
                          {fc.days_of_stock_remaining != null ? `${fc.days_of_stock_remaining}d stock` : 'no stock'}
                        </span>
                      </div>
                      {/* Mini sparkline bars */}
                      <div style={{ display: 'flex', gap: 3, alignItems: 'flex-end', height: 36 }}>
                        {(fc.forecasted_daily_demand || []).map((d, j) => (
                          <div key={j} style={{
                            flex: 1, background: fc.demand_spike_detected ? '#7c3aed' : '#f97316',
                            borderRadius: '2px 2px 0 0', opacity: 0.7 + (j / 14),
                            height: `${Math.max(8, (d / maxD) * 100)}%`
                          }} />
                        ))}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 5, fontSize: 11, color: '#6b7280' }}>
                        <span>avg {fc.avg_forecasted_demand} units/day</span>
                        <span style={{ color: fc.confidence >= 0.7 ? '#4ade80' : '#ca8a04' }}>conf {Math.round(fc.confidence * 100)}%</span>
                      </div>
                      {fc.spike_ratio && <div style={{ fontSize: 10, color: '#a78bfa', marginTop: 2 }}>demand {fc.spike_ratio}x prior avg</div>}
                    </div>
                  );
                })}
              </div>
            ) : <EmptyState icon="📈" text="No forecast data" />
          }
        </div>
      </div>

      {/* Chat */}
      <ChatInterface />
    </div>
  );
};

// ============================================================================
// PAGE: INVENTORY MANAGEMENT
// ============================================================================

const InventoryPage = () => {
  const [items, setItems] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null); // null | 'add' | { item }
  const [toast, setToast] = useState(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [form, setForm] = useState({ sku_id: '', name: '', category: '', warehouse_id: '', current_stock: '' });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [inv, wh] = await Promise.all([api('/inventory'), api('/warehouses')]);
      setItems(inv); setWarehouses(wh);
    } catch (e) { setToast({ msg: e.message, type: 'error' }); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openAdd = () => {
    setForm({ sku_id: '', name: '', category: '', warehouse_id: warehouses[0] || '', current_stock: '0' });
    setModal('add');
  };
  const openEdit = (item) => {
    setForm({ sku_id: item.sku_id, name: item.name, category: item.category || '', warehouse_id: warehouses[0] || '', current_stock: '' });
    setModal({ item });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (modal === 'add') {
        await api('/inventory', { method: 'POST', body: JSON.stringify({ sku_id: form.sku_id, name: form.name, category: form.category }) });
        setToast({ msg: `SKU ${form.sku_id} created`, type: 'success' });
      } else {
        const body = { name: form.name, category: form.category };
        if (form.warehouse_id && form.current_stock !== '') {
          body.warehouse_id = form.warehouse_id;
          body.current_stock = parseInt(form.current_stock);
        }
        await api(`/inventory/${modal.item.sku_id}`, { method: 'PUT', body: JSON.stringify(body) });
        setToast({ msg: `${modal.item.sku_id} updated`, type: 'success' });
      }
      setModal(null); load();
    } catch (e) { setToast({ msg: e.message, type: 'error' }); }
    finally { setSaving(false); }
  };

  const handleDelete = async (sku_id) => {
    if (!window.confirm(`Delete ${sku_id} and all its inventory? This cannot be undone.`)) return;
    setDeleting(sku_id);
    try {
      await api(`/inventory/${sku_id}`, { method: 'DELETE' });
      setToast({ msg: `${sku_id} deleted`, type: 'success' });
      load();
    } catch (e) { setToast({ msg: e.message, type: 'error' }); }
    finally { setDeleting(null); }
  };

  const filtered = items.filter(i =>
    i.sku_id.toLowerCase().includes(search.toLowerCase()) ||
    i.name?.toLowerCase().includes(search.toLowerCase()) ||
    i.category?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      {toast && <Toast msg={toast.msg} type={toast.type} onDone={() => setToast(null)} />}
      {modal && (
        <Modal title={modal === 'add' ? 'Add New SKU' : `Edit ${modal.item?.sku_id}`} onClose={() => setModal(null)}>
          {modal === 'add' && <FormField label="SKU ID" value={form.sku_id} onChange={v => setForm(f => ({...f, sku_id: v}))} placeholder="SKU100" required />}
          <FormField label="Name" value={form.name} onChange={v => setForm(f => ({...f, name: v}))} placeholder="Widget Type X" required />
          <FormField label="Category" value={form.category} onChange={v => setForm(f => ({...f, category: v}))} placeholder="Electronics" />
          {modal !== 'add' && (
            <>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 5 }}>Warehouse</label>
                <select value={form.warehouse_id} onChange={e => setForm(f => ({...f, warehouse_id: e.target.value}))} style={{
                  width: '100%', background: '#111827', border: '1px solid #374151', borderRadius: 8,
                  color: '#f1f5f9', padding: '9px 12px', fontSize: 14, outline: 'none'
                }}>
                  {warehouses.map(w => <option key={w} value={w}>{w}</option>)}
                </select>
              </div>
              <FormField label="New Stock Level (leave empty to keep unchanged)" value={form.current_stock} onChange={v => setForm(f => ({...f, current_stock: v}))} type="number" placeholder="0" />
            </>
          )}
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 8 }}>
            <Btn variant="ghost" onClick={() => setModal(null)}>Cancel</Btn>
            <Btn onClick={handleSave} loading={saving}>Save</Btn>
          </div>
        </Modal>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 800, color: '#f1f5f9' }}>Inventory Management</h1>
          <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: 14 }}>{items.length} SKUs tracked across all warehouses</p>
        </div>
        <Btn onClick={openAdd}>+ Add SKU</Btn>
      </div>

      <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search SKUs, names, categories…"
        style={{ width: '100%', background: '#1e2330', border: '1px solid #374151', borderRadius: 10, color: '#f1f5f9', padding: '11px 16px', fontSize: 14, outline: 'none', boxSizing: 'border-box', marginBottom: 20 }} />

      <div style={{ background: '#1e2330', border: '1px solid #1f2937', borderRadius: 14, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#111827' }}>
              {['SKU ID', 'Name', 'Category', 'Total Stock', 'Last Updated', ''].map(h => (
                <th key={h} style={{ padding: '13px 16px', textAlign: 'left', color: '#6b7280', fontSize: 12, fontWeight: 700, letterSpacing: '0.05em', borderBottom: '1px solid #1f2937' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}><Spinner /> Loading…</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={6}><EmptyState icon="📦" text="No SKUs found" /></td></tr>
            ) : filtered.map((item, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #111827' }}>
                <td style={{ padding: '13px 16px', color: '#f97316', fontWeight: 700, fontSize: 14 }}>{item.sku_id}</td>
                <td style={{ padding: '13px 16px', color: '#f1f5f9', fontSize: 14 }}>{item.name}</td>
                <td style={{ padding: '13px 16px' }}><Badge label={item.category || 'Uncategorized'} color="#374151" /></td>
                <td style={{ padding: '13px 16px', color: item.total_stock < 100 ? '#dc2626' : '#d1d5db', fontWeight: 700, fontSize: 15 }}>{item.total_stock?.toLocaleString()}</td>
                <td style={{ padding: '13px 16px', color: '#6b7280', fontSize: 12 }}>{fmtDate(item.updated_at)}</td>
                <td style={{ padding: '13px 16px' }}>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <Btn small variant="ghost" onClick={() => openEdit(item)}>✏️ Edit</Btn>
                    <Btn small variant="danger" loading={deleting === item.sku_id} onClick={() => handleDelete(item.sku_id)}>🗑</Btn>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ============================================================================
// PAGE: SUPPLIER MANAGEMENT
// ============================================================================

const SuppliersPage = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [toast, setToast] = useState(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [form, setForm] = useState({ supplier_id: '', name: '', region: '', avg_lead_time_days: '', on_time_delivery_pct: '', quality_score: '' });

  const load = useCallback(async () => {
    setLoading(true);
    try { setSuppliers(await api('/suppliers')); }
    catch (e) { setToast({ msg: e.message, type: 'error' }); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openAdd = () => {
    setForm({ supplier_id: '', name: '', region: '', avg_lead_time_days: '7', on_time_delivery_pct: '90', quality_score: '8' });
    setModal('add');
  };
  const openEdit = (s) => {
    setForm({ supplier_id: s.supplier_id, name: s.name, region: s.region || '', avg_lead_time_days: String(s.avg_lead_time_days || ''), on_time_delivery_pct: String(s.on_time_delivery_pct || ''), quality_score: String(s.quality_score || '') });
    setModal({ item: s });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (modal === 'add') {
        await api('/suppliers', { method: 'POST', body: JSON.stringify({
          supplier_id: form.supplier_id, name: form.name, region: form.region,
          avg_lead_time_days: parseFloat(form.avg_lead_time_days) || 0,
          on_time_delivery_pct: parseFloat(form.on_time_delivery_pct) || 100,
          quality_score: parseFloat(form.quality_score) || 8
        })});
        setToast({ msg: `Supplier ${form.supplier_id} created`, type: 'success' });
      } else {
        await api(`/suppliers/${modal.item.supplier_id}`, { method: 'PUT', body: JSON.stringify({
          name: form.name, region: form.region,
          avg_lead_time_days: parseFloat(form.avg_lead_time_days),
          on_time_delivery_pct: parseFloat(form.on_time_delivery_pct),
          quality_score: parseFloat(form.quality_score)
        })});
        setToast({ msg: `${modal.item.supplier_id} updated`, type: 'success' });
      }
      setModal(null); load();
    } catch (e) { setToast({ msg: e.message, type: 'error' }); }
    finally { setSaving(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(`Delete supplier ${id}?`)) return;
    setDeleting(id);
    try {
      await api(`/suppliers/${id}`, { method: 'DELETE' });
      setToast({ msg: `${id} deleted`, type: 'success' });
      load();
    } catch (e) { setToast({ msg: e.message, type: 'error' }); }
    finally { setDeleting(null); }
  };

  const filtered = suppliers.filter(s =>
    s.supplier_id.toLowerCase().includes(search.toLowerCase()) ||
    s.name?.toLowerCase().includes(search.toLowerCase()) ||
    s.region?.toLowerCase().includes(search.toLowerCase())
  );

  const getRiskFromScore = (score) => {
    if (score === null || score === undefined) return 'unknown';
    if (score >= 70) return 'low';
    if (score >= 40) return 'medium';
    return 'high';
  };

  const SupplierForm = () => (
    <>
      {modal === 'add' && <FormField label="Supplier ID" value={form.supplier_id} onChange={v => setForm(f => ({...f, supplier_id: v}))} placeholder="SUP021" required />}
      <FormField label="Company Name" value={form.name} onChange={v => setForm(f => ({...f, name: v}))} placeholder="Acme Supply Co." required />
      <FormField label="Region" value={form.region} onChange={v => setForm(f => ({...f, region: v}))} placeholder="Asia Pacific" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
        <FormField label="Avg Lead Time (days)" value={form.avg_lead_time_days} onChange={v => setForm(f => ({...f, avg_lead_time_days: v}))} type="number" placeholder="7" />
        <FormField label="On-Time Delivery %" value={form.on_time_delivery_pct} onChange={v => setForm(f => ({...f, on_time_delivery_pct: v}))} type="number" placeholder="90" />
        <FormField label="Quality Score (1-10)" value={form.quality_score} onChange={v => setForm(f => ({...f, quality_score: v}))} type="number" placeholder="8" />
      </div>
      <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 8 }}>
        <Btn variant="ghost" onClick={() => setModal(null)}>Cancel</Btn>
        <Btn onClick={handleSave} loading={saving}>Save</Btn>
      </div>
    </>
  );

  return (
    <div>
      {toast && <Toast msg={toast.msg} type={toast.type} onDone={() => setToast(null)} />}
      {modal && (
        <Modal title={modal === 'add' ? 'Add New Supplier' : `Edit ${modal.item?.supplier_id}`} onClose={() => setModal(null)} width={560}>
          <SupplierForm />
        </Modal>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 800, color: '#f1f5f9' }}>Supplier Management</h1>
          <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: 14 }}>{suppliers.length} active suppliers</p>
        </div>
        <Btn onClick={openAdd}>+ Add Supplier</Btn>
      </div>

      <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search suppliers, regions…"
        style={{ width: '100%', background: '#1e2330', border: '1px solid #374151', borderRadius: 10, color: '#f1f5f9', padding: '11px 16px', fontSize: 14, outline: 'none', boxSizing: 'border-box', marginBottom: 20 }} />

      <div style={{ background: '#1e2330', border: '1px solid #1f2937', borderRadius: 14, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#111827' }}>
              {['Supplier', 'Region', 'Lead Time', 'On-Time %', 'Quality', 'Risk Level', ''].map(h => (
                <th key={h} style={{ padding: '13px 16px', textAlign: 'left', color: '#6b7280', fontSize: 12, fontWeight: 700, letterSpacing: '0.05em', borderBottom: '1px solid #1f2937' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}><Spinner /></td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={7}><EmptyState icon="🏭" text="No suppliers found" /></td></tr>
            ) : filtered.map((s, i) => {
              const risk = s.risk_level || 'low';
              return (
                <tr key={i} style={{ borderBottom: '1px solid #111827' }}>
                  <td style={{ padding: '13px 16px' }}>
                    <div style={{ fontWeight: 700, color: '#f97316', fontSize: 14 }}>{s.supplier_id}</div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>{s.name}</div>
                  </td>
                  <td style={{ padding: '13px 16px', color: '#d1d5db', fontSize: 13 }}>{s.region || '—'}</td>
                  <td style={{ padding: '13px 16px', color: '#d1d5db', fontSize: 14, fontWeight: 600 }}>{fmt(s.avg_lead_time_days)} days</td>
                  <td style={{ padding: '13px 16px' }}>
                    <span style={{ color: s.on_time_delivery_pct >= 80 ? '#4ade80' : s.on_time_delivery_pct >= 60 ? '#facc15' : '#f87171', fontWeight: 700, fontSize: 15 }}>{fmt(s.on_time_delivery_pct)}%</span>
                  </td>
                  <td style={{ padding: '13px 16px', color: '#d1d5db', fontSize: 14 }}>{fmt(s.quality_score)}/10</td>
                  <td style={{ padding: '13px 16px' }}>
                    <Badge label={risk.toUpperCase()} color={getRiskColor(risk)} />
                  </td>
                  <td style={{ padding: '13px 16px' }}>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <Btn small variant="ghost" onClick={() => openEdit(s)}>✏️ Edit</Btn>
                      <Btn small variant="danger" loading={deleting === s.supplier_id} onClick={() => handleDelete(s.supplier_id)}>🗑</Btn>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ============================================================================
// PAGE: ACTION HISTORY
// ============================================================================

const ActionHistoryPage = () => {
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [toast, setToast] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try { setActions(await api('/actions/history')); }
      catch (e) { setToast({ msg: e.message, type: 'error' }); }
      finally { setLoading(false); }
    })();
  }, []);

  const STATUS_FILTERS = ['all', 'pending_approval', 'approved', 'rejected', 'executed'];
  const filtered = filter === 'all' ? actions : actions.filter(a => a.status === filter);

  const counts = {
    all: actions.length,
    pending_approval: actions.filter(a => a.status === 'pending_approval').length,
    approved: actions.filter(a => a.status === 'approved').length,
    rejected: actions.filter(a => a.status === 'rejected').length,
    executed: actions.filter(a => a.status === 'executed').length,
  };

  return (
    <div>
      {toast && <Toast msg={toast.msg} type={toast.type} onDone={() => setToast(null)} />}

      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 800, color: '#f1f5f9' }}>Action History</h1>
        <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: 14 }}>Full audit log of all agent-proposed and manually triggered actions</p>
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {STATUS_FILTERS.map(s => (
          <button key={s} onClick={() => setFilter(s)} style={{
            padding: '7px 16px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600,
            background: filter === s ? '#f97316' : '#1e2330',
            color: filter === s ? '#fff' : '#9ca3af',
            transition: 'all 0.15s'
          }}>
            {s === 'all' ? 'All' : s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
            {' '}<span style={{ opacity: 0.7 }}>({counts[s]})</span>
          </button>
        ))}
      </div>

      <div style={{ background: '#1e2330', border: '1px solid #1f2937', borderRadius: 14, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#111827' }}>
              {['Type', 'Details', 'Reasoning', 'Status', 'Created', 'Updated'].map(h => (
                <th key={h} style={{ padding: '13px 16px', textAlign: 'left', color: '#6b7280', fontSize: 12, fontWeight: 700, letterSpacing: '0.05em', borderBottom: '1px solid #1f2937' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}><Spinner /></td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={6}><EmptyState icon="📋" text="No actions found" /></td></tr>
            ) : filtered.map((a, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #111827' }}>
                <td style={{ padding: '13px 16px' }}>
                  <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 13 }}>
                    {a.action_type === 'reorder' ? '📦 Reorder' : '🔄 Switch Supplier'}
                  </span>
                </td>
                <td style={{ padding: '13px 16px' }}>
                  <div style={{ fontSize: 12, color: '#9ca3af' }}>
                    {Object.entries(a.details || {}).map(([k, v]) => (
                      <div key={k}><span style={{ color: '#6b7280' }}>{k}:</span> <strong style={{ color: '#d1d5db' }}>{String(v)}</strong></div>
                    ))}
                  </div>
                </td>
                <td style={{ padding: '13px 16px', fontSize: 12, color: '#9ca3af', maxWidth: 200 }}>{a.reasoning || '—'}</td>
                <td style={{ padding: '13px 16px' }}>
                  <Badge label={a.status?.replace(/_/g,' ').toUpperCase()} color={getStatusColor(a.status)} />
                </td>
                <td style={{ padding: '13px 16px', fontSize: 12, color: '#6b7280', whiteSpace: 'nowrap' }}>{fmtDate(a.created_at)}</td>
                <td style={{ padding: '13px 16px', fontSize: 12, color: '#6b7280', whiteSpace: 'nowrap' }}>{fmtDate(a.updated_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ============================================================================
// ROOT APP
// ============================================================================

export default function App() {
  const [page, setPage] = useState('dashboard');

  const pages = {
    dashboard: <DashboardPage />,
    inventory: <InventoryPage />,
    suppliers: <SuppliersPage />,
    history:   <ActionHistoryPage />,
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0f1117', fontFamily: "'Inter', system-ui, sans-serif", color: '#f1f5f9' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        body { margin: 0; background: #0f1117; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #374151; border-radius: 3px; }
      `}</style>

      <Sidebar active={page} onNav={setPage} />

      <main style={{ flex: 1, overflowY: 'auto', padding: '36px 40px', maxWidth: 1300 }}>
        {pages[page]}
      </main>
    </div>
  );
}
