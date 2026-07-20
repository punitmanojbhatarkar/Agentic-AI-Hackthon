import React, { useState, useEffect, useRef, useCallback } from 'react';

// ============================================================================
// CONFIG & UTILITIES
// ============================================================================

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000/api';

// Synthetic unit prices by category for business impact calculation
const UNIT_PRICES = {
  'Electronics': 89, 'Medical': 145, 'Industrial': 52,
  'Consumer': 34, 'Raw Materials': 18, 'Chemicals': 67,
  'Automotive': 112, 'Food': 12, 'Packaging': 8,
  'default': 45,
};

const getUnitPrice = (category) => UNIT_PRICES[category] || UNIT_PRICES['default'];

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
    case 'critical': return 'rgba(220,38,38,0.12)';
    case 'high':     return 'rgba(234,88,12,0.12)';
    case 'medium':   return 'rgba(202,138,4,0.12)';
    case 'low':      return 'rgba(22,163,74,0.12)';
    default:         return 'rgba(107,114,128,0.12)';
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

const fmtMoney = (n) => {
  if (!n && n !== 0) return '—';
  return n >= 1000000 ? `$${(n/1000000).toFixed(1)}M` : n >= 1000 ? `$${(n/1000).toFixed(0)}K` : `$${n}`;
};

const api = async (path, opts = {}) => {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`);
  return json;
};

// Multi-agent labeling: maps tool names → specialist agent
const AGENT_LABELS = {
  forecast_demand:           { icon: '📊', name: 'Risk Analyst Agent',   color: '#7c3aed' },
  predict_stockout:          { icon: '🔍', name: 'Investigator Agent',   color: '#0e7490' },
  supplier_risk_score:       { icon: '📊', name: 'Risk Analyst Agent',   color: '#7c3aed' },
  detect_delay_impact:       { icon: '🔍', name: 'Investigator Agent',   color: '#0e7490' },
  recommend_allocation:      { icon: '✅', name: 'Action Agent',         color: '#16a34a' },
  recommend_alternate_source:{ icon: '✅', name: 'Action Agent',         color: '#16a34a' },
  __planner__:               { icon: '🧭', name: 'Planner Agent',        color: '#f97316' },
  __critic__:                { icon: '🧐', name: 'Critic Agent',         color: '#ca8a04' },
};

const getAgentLabel = (tool) => AGENT_LABELS[tool] || { icon: '🤖', name: 'AI Agent', color: '#6b7280' };

// ============================================================================
// SHARED COMPONENTS
// ============================================================================

const Spinner = ({ size = 20, color = '#f97316' }) => (
  <div style={{
    width: size, height: size,
    border: `2px solid rgba(255,255,255,0.15)`,
    borderTop: `2px solid ${color}`,
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
    display: 'inline-block', flexShrink: 0,
  }} />
);

const Toast = ({ msg, type = 'success', onDone }) => {
  useEffect(() => { const t = setTimeout(onDone, 3000); return () => clearTimeout(t); }, [onDone]);
  const colors = { success: '#16a34a', error: '#dc2626', info: '#2563eb', warning: '#ca8a04' };
  return (
    <div style={{
      position: 'fixed', bottom: 24, right: 24, zIndex: 9999,
      background: colors[type] || colors.info, color: '#fff',
      padding: '13px 22px', borderRadius: 12, fontWeight: 700, fontSize: 14,
      boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
      animation: 'slideUp 0.3s ease-out',
      display: 'flex', alignItems: 'center', gap: 8,
    }}>{msg}</div>
  );
};

const Badge = ({ label, color }) => (
  <span style={{
    background: color, color: '#fff', padding: '3px 10px',
    borderRadius: 999, fontSize: 11, fontWeight: 700,
    letterSpacing: '0.05em', whiteSpace: 'nowrap', display: 'inline-block',
  }}>{label}</span>
);

const GlassCard = ({ children, style = {}, glow }) => (
  <div style={{
    background: 'rgba(30,35,48,0.85)',
    backdropFilter: 'blur(12px)',
    border: `1px solid ${glow ? glow + '44' : 'rgba(255,255,255,0.07)'}`,
    borderRadius: 16,
    boxShadow: glow ? `0 0 24px ${glow}22, 0 4px 24px rgba(0,0,0,0.3)` : '0 4px 24px rgba(0,0,0,0.2)',
    ...style,
  }}>
    {children}
  </div>
);

const Modal = ({ title, onClose, children, width = 480 }) => (
  <div style={{
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
    backdropFilter: 'blur(4px)',
  }} onClick={e => e.target === e.currentTarget && onClose()}>
    <div style={{
      background: '#1a1f2e', border: '1px solid rgba(249,115,22,0.2)',
      borderRadius: 18, padding: 32, width, maxWidth: '95vw', maxHeight: '90vh',
      overflowY: 'auto', boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
      animation: 'modalIn 0.2s ease-out',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h3 style={{ margin: 0, color: '#f1f5f9', fontSize: 18, fontWeight: 800 }}>{title}</h3>
        <button onClick={onClose} style={{
          background: 'rgba(255,255,255,0.08)', border: 'none', color: '#9ca3af',
          cursor: 'pointer', fontSize: 18, lineHeight: 1, width: 32, height: 32,
          borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>×</button>
      </div>
      {children}
    </div>
  </div>
);

const FormField = ({ label, value, onChange, type = 'text', placeholder = '', required = false }) => (
  <div style={{ marginBottom: 16 }}>
    <label style={{ display: 'block', color: '#9ca3af', fontSize: 12, fontWeight: 600, marginBottom: 6, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
      {label}{required && <span style={{ color: '#f97316' }}> *</span>}
    </label>
    <input
      type={type} value={value} onChange={e => onChange(e.target.value)}
      placeholder={placeholder} required={required}
      style={{
        width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 10, color: '#f1f5f9', padding: '10px 14px', fontSize: 14,
        outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.2s',
      }}
      onFocus={e => e.target.style.borderColor = '#f97316'}
      onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
    />
  </div>
);

const Btn = ({ children, onClick, variant = 'primary', loading = false, small = false, disabled = false }) => {
  const styles = {
    primary: { background: 'linear-gradient(135deg, #f97316, #ea580c)', color: '#fff', boxShadow: '0 4px 12px rgba(249,115,22,0.3)' },
    danger:  { background: 'linear-gradient(135deg, #dc2626, #b91c1c)', color: '#fff', boxShadow: '0 4px 12px rgba(220,38,38,0.3)' },
    ghost:   { background: 'rgba(255,255,255,0.06)', color: '#9ca3af', border: '1px solid rgba(255,255,255,0.1)' },
    success: { background: 'linear-gradient(135deg, #16a34a, #15803d)', color: '#fff', boxShadow: '0 4px 12px rgba(22,163,74,0.3)' },
    purple:  { background: 'linear-gradient(135deg, #7c3aed, #6d28d9)', color: '#fff', boxShadow: '0 4px 12px rgba(124,58,237,0.3)' },
  };
  return (
    <button onClick={onClick} disabled={loading || disabled} style={{
      ...styles[variant], border: 'none', borderRadius: 10,
      padding: small ? '6px 14px' : '10px 20px',
      fontSize: small ? 12 : 14, fontWeight: 700, cursor: 'pointer',
      display: 'inline-flex', alignItems: 'center', gap: 6,
      opacity: (loading || disabled) ? 0.6 : 1, transition: 'all 0.2s',
      transform: 'translateY(0)',
    }}
    onMouseEnter={e => { if (!loading && !disabled) e.currentTarget.style.transform = 'translateY(-1px)'; }}
    onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
    >
      {loading && <Spinner size={13} color="#fff" />}
      {children}
    </button>
  );
};

const EmptyState = ({ icon, text }) => (
  <div style={{ textAlign: 'center', padding: '44px 24px', color: '#4b5563' }}>
    <div style={{ fontSize: 38, marginBottom: 12, opacity: 0.7 }}>{icon}</div>
    <p style={{ margin: 0, fontSize: 14, color: '#6b7280' }}>{text}</p>
  </div>
);

const SkeletonRow = () => (
  <div style={{
    height: 56, background: 'linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.04) 75%)',
    backgroundSize: '200% 100%', borderRadius: 10, marginBottom: 10,
    animation: 'shimmer 1.5s infinite',
  }} />
);

// ============================================================================
// ANIMATED STAT CARD
// ============================================================================

const AnimatedNumber = ({ value, duration = 800 }) => {
  const [display, setDisplay] = useState(0);
  const isNum = typeof value === 'number';

  useEffect(() => {
    if (!isNum || value === 0) { setDisplay(value); return; }
    let start = 0;
    const step = value / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= value) { setDisplay(value); clearInterval(timer); }
      else { setDisplay(Math.floor(start)); }
    }, 16);
    return () => clearInterval(timer);
  }, [value, duration, isNum]);

  return <>{isNum ? display : value}</>;
};

const StatCard = ({ icon, label, value, sub, color = '#f97316', pulse = false }) => (
  <GlassCard style={{ padding: '20px 22px', display: 'flex', alignItems: 'center', gap: 16, transition: 'transform 0.2s' }}
    glow={pulse && color}>
    <div style={{
      fontSize: 28, width: 52, height: 52, display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: `${color}22`, borderRadius: 14, flexShrink: 0,
      animation: pulse ? 'subtlePulse 2s infinite' : 'none',
    }}>{icon}</div>
    <div>
      <div style={{ fontSize: 30, fontWeight: 900, color, lineHeight: 1 }}>
        <AnimatedNumber value={value} />
      </div>
      <div style={{ fontSize: 12, color: '#9ca3af', fontWeight: 700, marginTop: 3, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>{sub}</div>}
    </div>
  </GlassCard>
);

// ============================================================================
// MULTI-AGENT RESPONSE COMPONENT (upgraded)
// ============================================================================

const AgentResponse = ({ response }) => {
  const [show, setShow] = useState(false);
  if (!response) return null;
  const confColor = response.confidence === 'high' ? '#16a34a' : response.confidence === 'medium' ? '#ca8a04' : '#dc2626';
  return (
    <GlassCard style={{ padding: 18, maxWidth: 560 }} glow="#1d4ed8">
      <p style={{ margin: '0 0 12px', color: '#bfdbfe', fontSize: 14, lineHeight: 1.65 }}>
        {response.final_answer}
      </p>

      {response.execution_trace?.length > 0 && (
        <>
          <button onClick={() => setShow(s => !s)} style={{
            background: 'rgba(96,165,250,0.1)', border: '1px solid rgba(96,165,250,0.25)',
            color: '#60a5fa', cursor: 'pointer', fontSize: 12, fontWeight: 700,
            padding: '5px 12px', borderRadius: 8, marginBottom: show ? 12 : 0, display: 'flex', alignItems: 'center', gap: 6,
          }}>
            {show ? '▼' : '▶'} {show ? 'Hide' : 'Show'} agent reasoning ({response.execution_trace.length} steps)
          </button>

          {show && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
              {/* Planner agent — always shown as step 0 */}
              <div style={{
                background: 'rgba(249,115,22,0.1)', border: '1px solid rgba(249,115,22,0.2)',
                borderLeft: '3px solid #f97316', borderRadius: 8, padding: '8px 12px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <span style={{ fontSize: 14 }}>🧭</span>
                  <span style={{ fontSize: 11, fontWeight: 800, color: '#f97316', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Planner Agent</span>
                </div>
                <div style={{ fontSize: 12, color: '#9ca3af' }}>Analysed query → planned {response.execution_trace.length}-step investigation strategy</div>
              </div>

              {/* Each tool execution step */}
              {response.execution_trace.map((s, i) => {
                const agent = getAgentLabel(s.tool);
                return (
                  <div key={i} style={{
                    background: `${agent.color}11`,
                    border: `1px solid ${agent.color}33`,
                    borderLeft: `3px solid ${agent.color}`,
                    borderRadius: 8, padding: '8px 12px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                      <span style={{ fontSize: 14 }}>{agent.icon}</span>
                      <span style={{ fontSize: 11, fontWeight: 800, color: agent.color, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{agent.name}</span>
                      <span style={{ fontSize: 10, color: '#4b5563', marginLeft: 'auto' }}>Step {s.step}</span>
                    </div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>
                      <span style={{ color: '#d1d5db', fontWeight: 600 }}>{s.tool}</span> — {s.reasoning}
                    </div>
                    {s.error && <div style={{ fontSize: 11, color: '#fca5a5', marginTop: 4 }}>✗ {s.error}</div>}
                  </div>
                );
              })}

              {/* Critic agent — always shown as final step */}
              <div style={{
                background: 'rgba(202,138,4,0.1)', border: '1px solid rgba(202,138,4,0.2)',
                borderLeft: '3px solid #ca8a04', borderRadius: 8, padding: '8px 12px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <span style={{ fontSize: 14 }}>🧐</span>
                  <span style={{ fontSize: 11, fontWeight: 800, color: '#ca8a04', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Critic Agent</span>
                </div>
                <div style={{ fontSize: 12, color: '#9ca3af' }}>
                  Reviewed outputs → assigned <strong style={{ color: confColor }}>{response.confidence}</strong> confidence · {response.caveats || 'No caveats'}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      <div style={{
        display: 'flex', alignItems: 'center', gap: 6, paddingTop: 10,
        borderTop: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: confColor }} />
        <span style={{ fontSize: 11, color: '#60a5fa', fontWeight: 600 }}>{response.confidence} confidence</span>
        {response.caveats && <span style={{ fontSize: 11, color: '#4b5563', marginLeft: 8, fontStyle: 'italic' }}>· {response.caveats}</span>}
      </div>
    </GlassCard>
  );
};

// ============================================================================
// CHAT INTERFACE
// ============================================================================

const QUICK_QUESTIONS = [
  "What is causing today's biggest disruption?",
  "Which supplier has the highest risk?",
  "Which SKU is closest to stockout?",
  "Recommend an alternate source for SKU001",
];

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const send = async (question) => {
    const q = (question || input).trim();
    if (!q || loading) return;
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
    <GlassCard style={{ display: 'flex', flexDirection: 'column', minHeight: 480 }}>
      <div style={{
        padding: '18px 22px', borderBottom: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div style={{ fontWeight: 800, color: '#f1f5f9', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ background: 'linear-gradient(135deg,#f97316,#7c3aed)', borderRadius: 8, padding: '2px 8px', fontSize: 12 }}>AI</span>
          Ask SupplySense
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {QUICK_QUESTIONS.map((q, i) => (
            <button key={i} onClick={() => send(q)} disabled={loading} style={{
              background: 'rgba(249,115,22,0.12)', border: '1px solid rgba(249,115,22,0.25)',
              color: '#fb923c', borderRadius: 8, padding: '4px 10px', fontSize: 11, fontWeight: 600,
              cursor: 'pointer', whiteSpace: 'nowrap', opacity: loading ? 0.5 : 1,
            }}>{q.length > 30 ? q.slice(0, 28) + '…' : q}</button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#4b5563', fontSize: 13, padding: '40px 0' }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>🧠</div>
            <div>Ask about inventory, disruptions, or supplier risks…</div>
            <div style={{ color: '#374151', fontSize: 12, marginTop: 8 }}>4-agent AI team ready: Planner · Investigator · Risk Analyst · Action Agent</div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            {m.role === 'user' ? (
              <div style={{
                background: 'linear-gradient(135deg, #f97316, #ea580c)',
                color: '#fff', borderRadius: '16px 16px 4px 16px',
                padding: '10px 16px', maxWidth: 380, fontSize: 14, fontWeight: 500,
                boxShadow: '0 4px 12px rgba(249,115,22,0.3)',
              }}>{m.content}</div>
            ) : m.role === 'error' ? (
              <div style={{
                background: 'rgba(127,29,29,0.5)', color: '#fca5a5',
                borderRadius: 12, padding: '10px 16px', fontSize: 14,
                border: '1px solid rgba(220,38,38,0.3)',
              }}>⚠️ {m.content}</div>
            ) : (
              <AgentResponse response={m.content} />
            )}
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{
              background: 'rgba(55,65,81,0.6)', color: '#d1d5db',
              borderRadius: '16px 16px 16px 4px', padding: '12px 18px',
              fontSize: 13, display: 'flex', gap: 8, alignItems: 'center',
              border: '1px solid rgba(255,255,255,0.06)',
            }}>
              <Spinner size={13} />
              <span>Multi-agent team is reasoning…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={e => { e.preventDefault(); send(); }} style={{
        padding: 16, borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', gap: 10,
      }}>
        <input value={input} onChange={e => setInput(e.target.value)} disabled={loading}
          placeholder="What is causing today's biggest disruption?"
          style={{
            flex: 1, background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 10, color: '#f1f5f9', padding: '11px 16px', fontSize: 14, outline: 'none',
            transition: 'border-color 0.2s',
          }}
          onFocus={e => e.target.style.borderColor = '#f97316'}
          onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
        />
        <Btn disabled={!input.trim()} loading={loading}>Send</Btn>
      </form>
    </GlassCard>
  );
};

// ============================================================================
// WHAT-IF SIMULATION LAB 🔮
// ============================================================================

const WhatIfLab = ({ skus, suppliers }) => {
  const [scenarioType, setScenarioType] = useState('demand_spike');
  const [selectedId, setSelectedId] = useState('');
  const [multiplier, setMultiplier] = useState(1.5);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const ids = scenarioType === 'demand_spike' ? skus : suppliers;

  useEffect(() => {
    setSelectedId(ids[0] || '');
    setResult(null);
  }, [scenarioType]);

  const runSimulation = async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const body = scenarioType === 'demand_spike'
        ? { type: 'demand_spike', sku_id: selectedId, multiplier }
        : { type: 'supplier_delay', supplier_id: selectedId, multiplier };
      const data = await api('/simulate', { method: 'POST', body: JSON.stringify(body) });
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const sevColor = (sev) => sev === 'critical' ? '#dc2626' : sev === 'high' ? '#ea580c' : '#ca8a04';

  return (
    <GlassCard style={{ padding: 24 }} glow="#7c3aed">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
        <div style={{ fontSize: 24 }}>🔮</div>
        <div>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 800, color: '#f1f5f9' }}>What-If Simulation Lab</h3>
          <div style={{ fontSize: 11, color: '#7c3aed', fontWeight: 600, marginTop: 1 }}>AGENTIC AI FORECASTING ENGINE</div>
        </div>
      </div>

      {/* Scenario type toggle */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {[
          { id: 'demand_spike', label: '⚡ Demand Spike', icon: '📈' },
          { id: 'supplier_delay', label: '🚛 Supplier Delay', icon: '⏱️' },
        ].map(s => (
          <button key={s.id} onClick={() => setScenarioType(s.id)} style={{
            flex: 1, padding: '10px 14px', borderRadius: 10, border: 'none', cursor: 'pointer',
            background: scenarioType === s.id ? 'linear-gradient(135deg,#7c3aed,#6d28d9)' : 'rgba(255,255,255,0.06)',
            color: scenarioType === s.id ? '#fff' : '#9ca3af',
            fontWeight: 700, fontSize: 13, transition: 'all 0.2s',
            boxShadow: scenarioType === s.id ? '0 4px 12px rgba(124,58,237,0.4)' : 'none',
          }}>{s.label}</button>
        ))}
      </div>

      {/* Target selector */}
      <div style={{ marginBottom: 14 }}>
        <label style={{ display: 'block', color: '#9ca3af', fontSize: 11, fontWeight: 700, marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {scenarioType === 'demand_spike' ? 'Select SKU' : 'Select Supplier'}
        </label>
        <select value={selectedId} onChange={e => setSelectedId(e.target.value)} style={{
          width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 10, color: '#f1f5f9', padding: '10px 14px', fontSize: 14, outline: 'none',
        }}>
          {ids.map(id => <option key={id} value={id}>{id}</option>)}
        </select>
      </div>

      {/* Multiplier slider */}
      <div style={{ marginBottom: 20 }}>
        <label style={{ display: 'flex', justifyContent: 'space-between', color: '#9ca3af', fontSize: 11, fontWeight: 700, marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          <span>{scenarioType === 'demand_spike' ? 'Demand Multiplier' : 'Lead Time Multiplier'}</span>
          <span style={{ color: '#a78bfa', fontSize: 15, fontWeight: 900 }}>{multiplier}×</span>
        </label>
        <input type="range" min="1.1" max="3.0" step="0.1" value={multiplier}
          onChange={e => setMultiplier(parseFloat(e.target.value))}
          style={{ width: '100%', accentColor: '#7c3aed', cursor: 'pointer' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#4b5563', marginTop: 4 }}>
          <span>1.1× (mild)</span><span>2× (double)</span><span>3× (extreme)</span>
        </div>
      </div>

      <Btn variant="purple" onClick={runSimulation} loading={loading} style={{ width: '100%', justifyContent: 'center' }}>
        {loading ? 'Running AI Simulation…' : '🔮 Run What-If Simulation'}
      </Btn>

      {error && (
        <div style={{ marginTop: 16, background: 'rgba(220,38,38,0.1)', border: '1px solid rgba(220,38,38,0.3)', borderRadius: 10, padding: 12, fontSize: 13, color: '#fca5a5' }}>
          ⚠️ {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 20, animation: 'fadeIn 0.4s ease-out' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
            {/* Before */}
            <div style={{ background: 'rgba(22,163,74,0.08)', border: '1px solid rgba(22,163,74,0.25)', borderRadius: 12, padding: 14 }}>
              <div style={{ fontSize: 10, fontWeight: 800, color: '#4ade80', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10 }}>📊 Current State</div>
              {result.scenario === 'demand_spike' ? (
                <>
                  <div style={{ fontSize: 22, fontWeight: 900, color: '#4ade80' }}>{result.before.days_until_stockout}d</div>
                  <div style={{ fontSize: 10, color: '#6b7280', marginBottom: 6 }}>days until stockout</div>
                  <div style={{ fontSize: 13, color: '#9ca3af' }}>{result.before.avg_daily_demand} units/day</div>
                </>
              ) : (
                <>
                  <div style={{ fontSize: 22, fontWeight: 900, color: '#4ade80' }}>{result.before.score}</div>
                  <div style={{ fontSize: 10, color: '#6b7280', marginBottom: 6 }}>risk score</div>
                  <Badge label={result.before.risk_category.toUpperCase()} color={getRiskColor(result.before.risk_category)} />
                </>
              )}
            </div>

            {/* After */}
            <div style={{ background: 'rgba(220,38,38,0.08)', border: `1px solid ${sevColor(result.impact.severity)}55`, borderRadius: 12, padding: 14 }}>
              <div style={{ fontSize: 10, fontWeight: 800, color: sevColor(result.impact.severity), textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10 }}>
                🔮 If {multiplier}× scenario
              </div>
              {result.scenario === 'demand_spike' ? (
                <>
                  <div style={{ fontSize: 22, fontWeight: 900, color: sevColor(result.impact.severity) }}>{result.after.days_until_stockout}d</div>
                  <div style={{ fontSize: 10, color: '#6b7280', marginBottom: 6 }}>days until stockout</div>
                  <div style={{ fontSize: 13, color: '#9ca3af' }}>{result.after.avg_daily_demand} units/day</div>
                </>
              ) : (
                <>
                  <div style={{ fontSize: 22, fontWeight: 900, color: sevColor(result.impact.severity) }}>{result.after.score}</div>
                  <div style={{ fontSize: 10, color: '#6b7280', marginBottom: 6 }}>risk score</div>
                  <Badge label={result.after.risk_category.toUpperCase()} color={getRiskColor(result.after.risk_category)} />
                </>
              )}
            </div>
          </div>

          {/* Impact summary */}
          <div style={{
            background: `${sevColor(result.impact.severity)}15`,
            border: `1px solid ${sevColor(result.impact.severity)}44`,
            borderRadius: 12, padding: 14,
          }}>
            <div style={{ fontWeight: 800, color: sevColor(result.impact.severity), fontSize: 13, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <span>⚡</span> Impact Analysis
              <Badge label={result.impact.severity.toUpperCase()} color={sevColor(result.impact.severity)} />
            </div>
            {result.scenario === 'demand_spike' ? (
              <div style={{ fontSize: 13, color: '#d1d5db', lineHeight: 1.6 }}>
                Demand increases by <strong style={{ color: '#f87171' }}>+{result.impact.demand_increase_units} units/day</strong>.
                Stockout risk advances by <strong style={{ color: '#f87171' }}>{result.impact.stockout_days_lost} days</strong>.
                {result.after.days_until_stockout < 7 && <span style={{ color: '#fca5a5' }}> Immediate reorder action required!</span>}
              </div>
            ) : (
              <div style={{ fontSize: 13, color: '#d1d5db', lineHeight: 1.6 }}>
                Risk score drops by <strong style={{ color: '#f87171' }}>{result.impact.score_drop} points</strong>.
                {result.impact.risk_escalated && <span style={{ color: '#fca5a5' }}> Risk level escalates to <strong>{result.after.risk_category.toUpperCase()}</strong>. Activate backup supplier plan!</span>}
              </div>
            )}
          </div>
        </div>
      )}
    </GlassCard>
  );
};

// ============================================================================
// LIVE INTELLIGENCE FEED
// ============================================================================

const ActivityFeed = ({ sweep, shipmentDelays, demandForecast }) => {
  const events = [];

  if (sweep?.risky_suppliers) {
    sweep.risky_suppliers.slice(0, 3).forEach(s => {
      events.push({
        icon: '📊', color: getRiskColor(s.risk_category),
        text: `Risk Analyst flagged ${s.supplier_id} as ${s.risk_category?.toUpperCase()} risk`,
        sub: `Score: ${fmt(s.score)} · ${fmt(s.breakdown?.on_time_delivery_pct)}% on-time`,
        ts: new Date(),
      });
    });
  }

  if (sweep?.critical_stockouts) {
    sweep.critical_stockouts.slice(0, 3).forEach(s => {
      if (s.demand_spike_detected) {
        events.push({
          icon: '⚡', color: '#7c3aed',
          text: `Demand spike detected: ${s.sku_id}`,
          sub: `Reorder ${s.recommended_reorder_quantity} units · ${s.days_until_stockout}d remaining`,
          ts: new Date(),
        });
      } else {
        events.push({
          icon: '📦', color: getRiskColor(s.risk_level),
          text: `Stockout risk: ${s.sku_id} @ ${s.warehouse_id}`,
          sub: `${s.days_until_stockout}d remaining · Reorder ${s.recommended_reorder_quantity}u`,
          ts: new Date(),
        });
      }
    });
  }

  if (shipmentDelays) {
    shipmentDelays.slice(0, 2).forEach(s => {
      events.push({
        icon: '🚛', color: getRiskColor(s.severity),
        text: `Shipment delayed: ${s.shipment_id}`,
        sub: `${s.delay_days} days late · ${s.current_status}`,
        ts: new Date(),
      });
    });
  }

  if (events.length === 0) {
    return (
      <GlassCard style={{ padding: 24 }}>
        <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15, fontWeight: 800, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#16a34a', display: 'inline-block', animation: 'subtlePulse 2s infinite' }} />
          Live Intelligence Feed
        </h3>
        <EmptyState icon="🛡️" text="All systems nominal — no active alerts" />
      </GlassCard>
    );
  }

  return (
    <GlassCard style={{ padding: 24 }}>
      <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15, fontWeight: 800, display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ea580c', display: 'inline-block', animation: 'subtlePulse 1.5s infinite' }} />
        Live Intelligence Feed
        <span style={{ marginLeft: 'auto', fontSize: 11, color: '#4b5563', fontWeight: 500 }}>{events.length} events</span>
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 380, overflowY: 'auto' }}>
        {events.map((ev, i) => (
          <div key={i} style={{
            display: 'flex', gap: 12, alignItems: 'flex-start',
            padding: '10px 12px',
            background: 'rgba(0,0,0,0.2)', borderRadius: 10,
            borderLeft: `3px solid ${ev.color}`,
            animation: `fadeIn 0.3s ease-out ${i * 0.05}s both`,
          }}>
            <div style={{ fontSize: 18, flexShrink: 0 }}>{ev.icon}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, color: '#e5e7eb', fontWeight: 600, marginBottom: 2 }}>{ev.text}</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>{ev.sub}</div>
            </div>
            <div style={{ fontSize: 10, color: '#374151', flexShrink: 0, whiteSpace: 'nowrap' }}>just now</div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
};

// ============================================================================
// SIDEBAR NAVIGATION
// ============================================================================

const NAV_ITEMS = [
  { id: 'dashboard',  label: 'Dashboard',      icon: '📊' },
  { id: 'inventory',  label: 'Inventory',      icon: '📦' },
  { id: 'suppliers',  label: 'Suppliers',      icon: '🏭' },
  { id: 'history',    label: 'Action History', icon: '📋' },
];

const Sidebar = ({ active, onNav }) => (
  <aside style={{
    width: 230, background: 'rgba(10,13,22,0.95)',
    borderRight: '1px solid rgba(255,255,255,0.06)',
    display: 'flex', flexDirection: 'column', flexShrink: 0,
    height: '100vh', position: 'sticky', top: 0,
    backdropFilter: 'blur(20px)',
  }}>
    {/* Logo */}
    <div style={{ padding: '28px 22px 22px' }}>
      <div style={{
        fontSize: 22, fontWeight: 900, letterSpacing: '-0.5px',
        background: 'linear-gradient(135deg, #f97316, #fbbf24)',
        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
      }}>
        SupplySense
      </div>
      <div style={{ fontSize: 10, color: '#4b5563', marginTop: 2, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
        AI Supply Chain Intelligence
      </div>
    </div>

    {/* Agent status badge */}
    <div style={{
      margin: '0 14px 16px', padding: '8px 14px',
      background: 'rgba(22,163,74,0.12)', border: '1px solid rgba(22,163,74,0.25)',
      borderRadius: 10, display: 'flex', alignItems: 'center', gap: 8,
    }}>
      <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#16a34a', animation: 'subtlePulse 2s infinite' }} />
      <div>
        <div style={{ fontSize: 11, color: '#4ade80', fontWeight: 700 }}>4 Agents Online</div>
        <div style={{ fontSize: 10, color: '#374151' }}>Planner · Analyst · Action · Critic</div>
      </div>
    </div>

    <nav style={{ flex: 1, padding: '0 10px' }}>
      {NAV_ITEMS.map(item => (
        <button key={item.id} onClick={() => onNav(item.id)} style={{
          display: 'flex', alignItems: 'center', gap: 12, width: '100%',
          padding: '11px 14px', marginBottom: 4, border: 'none', borderRadius: 12,
          background: active === item.id
            ? 'linear-gradient(135deg, rgba(249,115,22,0.2), rgba(234,88,12,0.1))'
            : 'transparent',
          boxShadow: active === item.id ? 'inset 0 0 0 1px rgba(249,115,22,0.3)' : 'none',
          color: active === item.id ? '#f97316' : '#6b7280',
          fontSize: 14, fontWeight: active === item.id ? 700 : 500,
          cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s',
        }}>
          <span style={{ fontSize: 18 }}>{item.icon}</span>
          {item.label}
          {active === item.id && (
            <div style={{ marginLeft: 'auto', width: 6, height: 6, borderRadius: '50%', background: '#f97316', boxShadow: '0 0 8px #f97316' }} />
          )}
        </button>
      ))}
    </nav>

    <div style={{ padding: '14px 22px', borderTop: '1px solid rgba(255,255,255,0.04)', fontSize: 10, color: '#374151', fontWeight: 500 }}>
      SupplySense v2.0 · Hackathon 2026
    </div>
  </aside>
);

// ============================================================================
// PAGE: DASHBOARD
// ============================================================================

const DashboardPage = () => {
  const [sweep, setSweep] = useState(null);
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actLoading, setActLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [expandedSup, setExpandedSup] = useState(null);
  const [skuList, setSkuList] = useState([]);
  const [supplierList, setSupplierList] = useState([]);

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

  const fetchLists = useCallback(async () => {
    try {
      const [skus, sups] = await Promise.all([api('/inventory'), api('/suppliers')]);
      setSkuList(skus.map(s => s.sku_id));
      setSupplierList(sups.map(s => s.supplier_id));
    } catch (e) { /* silent */ }
  }, []);

  useEffect(() => {
    fetchSweep(); fetchActions(); fetchPanels(); fetchLists();
  }, [fetchSweep, fetchActions, fetchPanels, fetchLists]);

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
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: 0, fontSize: 32, fontWeight: 900, color: '#f1f5f9', letterSpacing: '-0.5px' }}>Operations Dashboard</h1>
        <p style={{ margin: '6px 0 0', color: '#4b5563', fontSize: 13 }}>
          {sweep?.timestamp ? `Last intelligence sweep: ${fmtDate(sweep.timestamp)}` : loading ? 'Running sweep…' : 'Ready — click Refresh to run a sweep'}
        </p>
      </div>

      {/* KPI Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        <StatCard icon="🔴" label="Critical Stockouts" value={stats.critical_count ?? '—'} color="#dc2626" pulse={stats.critical_count > 0} />
        <StatCard icon="🟠" label="High Risk SKUs" value={stats.high_count ?? '—'} color="#ea580c" pulse={stats.high_count > 0} />
        <StatCard icon="⚠️" label="Risky Suppliers" value={stats.risky_supplier_count ?? '—'} color="#ca8a04" />
        <StatCard icon="🤖" label="Pending Actions" value={actions.length} color="#f97316" />
      </div>

      {/* Executive Summary */}
      <GlassCard style={{ padding: '22px 26px', marginBottom: 28 }} glow="#f97316">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <h2 style={{ margin: 0, fontSize: 17, fontWeight: 800, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: 8 }}>
            🧠 Executive Summary
            <span style={{ fontSize: 10, background: 'rgba(249,115,22,0.2)', color: '#f97316', padding: '2px 8px', borderRadius: 6, fontWeight: 700 }}>AI GENERATED</span>
          </h2>
          <Btn onClick={fetchSweep} loading={loading} small>{loading ? 'Analyzing…' : '↻ Refresh'}</Btn>
        </div>
        {loading ? (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', color: '#7c3aed', fontSize: 14 }}>
            <Spinner size={14} color="#7c3aed" /> 4-agent team running intelligence sweep…
          </div>
        ) : sweep?.executive_summary ? (
          <p style={{ margin: 0, color: '#bfdbfe', fontSize: 14, lineHeight: 1.75, whiteSpace: 'pre-line' }}>
            {sweep.executive_summary}
          </p>
        ) : (
          <p style={{ margin: 0, color: '#4b5563' }}>No analysis available yet. Click Refresh to run a sweep.</p>
        )}
      </GlassCard>

      {/* Main 3-panel row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(310px, 1fr))', gap: 20, marginBottom: 24 }}>

        {/* Critical Inventory Shortages */}
        <GlassCard style={{ padding: 22 }}>
          <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15, fontWeight: 800 }}>📦 Inventory Shortages</h3>
          {loading ? [1,2,3].map(i => <SkeletonRow key={i} />) :
            sweep?.critical_stockouts?.length > 0 ? (
              <div style={{ maxHeight: 400, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[...(sweep.critical_stockouts)].sort((a,b) => {
                  const o = { critical:0, high:1, medium:2 };
                  return (o[a.risk_level]??9) - (o[b.risk_level]??9);
                }).map((s, i) => {
                  const unitPrice = getUnitPrice(s.category);
                  const revenueAtRisk = s.recommended_reorder_quantity ? Math.round(s.recommended_reorder_quantity * unitPrice) : null;
                  return (
                    <div key={i} style={{
                      background: getRiskBg(s.risk_level),
                      border: `1px solid ${getRiskColor(s.risk_level)}33`,
                      borderLeft: `4px solid ${getRiskColor(s.risk_level)}`,
                      borderRadius: 12, padding: 14,
                      animation: s.risk_level === 'critical' ? 'criticalPulse 3s infinite' : 'none',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, flexWrap: 'wrap', gap: 4 }}>
                        <span style={{ fontWeight: 800, color: '#f1f5f9', fontSize: 14 }}>{s.sku_id}</span>
                        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                          {s.demand_spike_detected && <Badge label="⚡ DEMAND SPIKE" color="#7c3aed" />}
                          {s.overstock_risk && <Badge label="📈 OVERSTOCK" color="#0e7490" />}
                          <Badge label={s.risk_level?.toUpperCase()} color={getRiskColor(s.risk_level)} />
                        </div>
                      </div>
                      <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 6 }}>@ {s.warehouse_id}</div>
                      <div style={{ fontSize: 26, fontWeight: 900, color: '#fb923c' }}>{fmt(s.days_until_stockout)}</div>
                      <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 6 }}>days until stockout</div>
                      {revenueAtRisk && (
                        <div style={{ fontSize: 12, color: '#fca5a5', fontWeight: 700, background: 'rgba(220,38,38,0.1)', borderRadius: 6, padding: '4px 8px', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                          💰 Revenue at risk: <strong>{fmtMoney(revenueAtRisk)}</strong>
                        </div>
                      )}
                      <div style={{ fontSize: 12, color: '#d1d5db', background: 'rgba(0,0,0,0.2)', borderRadius: 8, padding: '6px 10px' }}>
                        Reorder: <strong>{fmt(s.recommended_reorder_quantity, 0)}</strong> units
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : <EmptyState icon="✅" text="No critical shortages detected" />
          }
        </GlassCard>

        {/* Supplier Risk */}
        <GlassCard style={{ padding: 22 }}>
          <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15, fontWeight: 800 }}>⚠️ Supplier Risk</h3>
          {loading ? [1,2].map(i => <SkeletonRow key={i} />) :
            sweep?.risky_suppliers?.length > 0 ? (
              <div style={{ maxHeight: 400, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {sweep.risky_suppliers.map((s, i) => {
                  const procurementRisk = s.breakdown?.on_time_delivery_pct != null
                    ? Math.round((100 - s.breakdown.on_time_delivery_pct) * 850)
                    : null;
                  return (
                    <div key={i} style={{
                      background: getRiskBg(s.risk_category),
                      border: `1px solid ${getRiskColor(s.risk_category)}33`,
                      borderLeft: `4px solid ${getRiskColor(s.risk_category)}`,
                      borderRadius: 12, padding: 14, cursor: 'pointer', transition: 'all 0.15s',
                    }} onClick={() => setExpandedSup(expandedSup === i ? null : i)}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 800, color: '#f1f5f9', fontSize: 14 }}>{s.supplier_id}</span>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <span style={{ fontSize: 12, color: '#9ca3af' }}>Score: {fmt(s.score)}</span>
                          <Badge label={s.risk_category?.toUpperCase()} color={getRiskColor(s.risk_category)} />
                        </div>
                      </div>
                      {procurementRisk > 0 && (
                        <div style={{ fontSize: 11, color: '#fca5a5', fontWeight: 600, marginTop: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                          💰 Procurement risk: ~{fmtMoney(procurementRisk)}/month
                        </div>
                      )}
                      {expandedSup === i && s.breakdown && (
                        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', flexDirection: 'column', gap: 6 }}>
                          {[
                            ['On-time delivery', `${fmt(s.breakdown.on_time_delivery_pct)}%`],
                            ['Lead time variance', `${fmt(s.breakdown.lead_time_variance_days)} days`],
                            ['Quality score', `${fmt(s.breakdown.avg_quality_score)}/100`],
                          ].map(([k, v]) => (
                            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                              <span style={{ color: '#6b7280' }}>{k}</span>
                              <span style={{ color: '#d1d5db', fontWeight: 700 }}>{v}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : <EmptyState icon="✅" text="No high-risk suppliers detected" />
          }
        </GlassCard>

        {/* Pending Actions */}
        <GlassCard style={{ padding: 22 }}>
          <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15, fontWeight: 800 }}>🤖 Agent Actions</h3>
          {actLoading ? [1,2].map(i => <SkeletonRow key={i} />) :
            actions.length > 0 ? (
              <div style={{ maxHeight: 400, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {actions.map((a, i) => (
                  <div key={i} style={{
                    background: 'rgba(37,99,235,0.08)',
                    border: '1px solid rgba(37,99,235,0.25)',
                    borderLeft: '4px solid #2563eb', borderRadius: 12, padding: 14,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 13 }}>
                        {a.action_type === 'reorder' ? '📦 Reorder Stock' : '🔄 Switch Supplier'}
                      </span>
                      <Badge label={a.status?.replace(/_/g,' ').toUpperCase()} color={getStatusColor(a.status)} />
                    </div>
                    <div style={{ fontSize: 12, color: '#9ca3af', background: 'rgba(0,0,0,0.2)', borderRadius: 8, padding: '6px 10px', marginBottom: 8 }}>
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
        </GlassCard>
      </div>

      {/* Second row: Shipment Delays + Warehouse + Demand Forecast */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(310px, 1fr))', gap: 20, marginBottom: 24 }}>

        {/* Shipment Delays */}
        <GlassCard style={{ padding: 22 }}>
          <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15, fontWeight: 800 }}>🚛 Shipment Delays</h3>
          {panelLoading ? [1,2].map(i => <SkeletonRow key={i} />) :
            shipmentDelays.length > 0 ? (
              <div style={{ maxHeight: 340, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {shipmentDelays.slice(0,10).map((sh, i) => (
                  <div key={i} style={{
                    background: getRiskBg(sh.severity),
                    border: `1px solid ${getRiskColor(sh.severity)}33`,
                    borderLeft: `4px solid ${getRiskColor(sh.severity)}`, borderRadius: 12, padding: 12,
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
                    <div style={{ fontSize: 22, fontWeight: 900, color: '#f87171' }}>{sh.delay_days} days late</div>
                  </div>
                ))}
              </div>
            ) : <EmptyState icon="✅" text="No active delays detected" />
          }
        </GlassCard>

        {/* Warehouse Utilization */}
        <GlassCard style={{ padding: 22 }}>
          <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15, fontWeight: 800 }}>🏭 Warehouse Utilization</h3>
          {panelLoading ? [1,2].map(i => <SkeletonRow key={i} />) :
            warehouseUtil.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {warehouseUtil.map((w, i) => {
                  const pct = w.utilization_pct;
                  const barColor = pct >= 90 ? '#dc2626' : pct >= 70 ? '#ca8a04' : '#16a34a';
                  return (
                    <div key={i}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, alignItems: 'baseline' }}>
                        <div>
                          <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 13 }}>{w.warehouse_id}</span>
                          <span style={{ color: '#6b7280', fontSize: 11, marginLeft: 6 }}>{w.name}</span>
                        </div>
                        <span style={{ fontWeight: 900, color: barColor, fontSize: 16 }}>{pct}%</span>
                      </div>
                      <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: 999, height: 8, overflow: 'hidden' }}>
                        <div style={{
                          width: `${Math.min(pct, 100)}%`, height: '100%',
                          background: `linear-gradient(90deg, ${barColor}88, ${barColor})`,
                          borderRadius: 999, transition: 'width 0.8s ease',
                        }} />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: 11, color: '#6b7280' }}>
                        <span>{w.total_stock?.toLocaleString()} units stored</span>
                        <span>cap: {w.capacity?.toLocaleString()}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : <EmptyState icon="🏭" text="No warehouse data" />
          }
        </GlassCard>

        {/* Demand Forecast */}
        <GlassCard style={{ padding: 22 }}>
          <h3 style={{ margin: '0 0 4px', color: '#f1f5f9', fontSize: 15, fontWeight: 800 }}>📈 7-Day Demand Forecast</h3>
          <div style={{ fontSize: 11, color: '#4b5563', marginBottom: 14 }}>Top 5 highest-risk SKUs by stock remaining</div>
          {panelLoading ? [1,2,3].map(i => <SkeletonRow key={i} />) :
            demandForecast.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxHeight: 340, overflowY: 'auto' }}>
                {demandForecast.map((fc, i) => {
                  const maxD = Math.max(...(fc.forecasted_daily_demand || [1]));
                  const trendIcon = fc.trend === 'increasing' ? '↑' : fc.trend === 'decreasing' ? '↓' : '→';
                  const trendColor = fc.trend === 'increasing' ? '#f87171' : fc.trend === 'decreasing' ? '#4ade80' : '#9ca3af';
                  return (
                    <div key={i} style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 10, padding: '12px 14px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                          <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 13 }}>{fc.sku_id}</span>
                          <span style={{ color: trendColor, fontSize: 14, fontWeight: 900 }}>{trendIcon}</span>
                          {fc.demand_spike_detected && <Badge label="⚡ SPIKE" color="#7c3aed" />}
                        </div>
                        <span style={{ fontSize: 11, color: '#6b7280' }}>
                          {fc.days_of_stock_remaining != null ? `${fc.days_of_stock_remaining}d stock` : 'no stock'}
                        </span>
                      </div>
                      <div style={{ display: 'flex', gap: 3, alignItems: 'flex-end', height: 36 }}>
                        {(fc.forecasted_daily_demand || []).map((d, j) => (
                          <div key={j} style={{
                            flex: 1,
                            background: fc.demand_spike_detected
                              ? `linear-gradient(to top, #7c3aed, #a78bfa)`
                              : `linear-gradient(to top, #ea580c, #f97316)`,
                            borderRadius: '3px 3px 0 0', opacity: 0.7 + (j / 14),
                            height: `${Math.max(8, (d / maxD) * 100)}%`,
                          }} />
                        ))}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 5, fontSize: 11, color: '#6b7280' }}>
                        <span>avg {fc.avg_forecasted_demand} units/day</span>
                        <span style={{ color: fc.confidence >= 0.7 ? '#4ade80' : '#ca8a04' }}>conf {Math.round(fc.confidence * 100)}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : <EmptyState icon="📈" text="No forecast data" />
          }
        </GlassCard>
      </div>

      {/* What-If Lab + Activity Feed Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <WhatIfLab skus={skuList} suppliers={supplierList} />
        <ActivityFeed sweep={sweep} shipmentDelays={shipmentDelays} demandForecast={demandForecast} />
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
  const [modal, setModal] = useState(null);
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
    if (!window.confirm(`Delete ${sku_id} and all its inventory?`)) return;
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
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', color: '#9ca3af', fontSize: 12, fontWeight: 600, marginBottom: 6, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Warehouse</label>
                <select value={form.warehouse_id} onChange={e => setForm(f => ({...f, warehouse_id: e.target.value}))} style={{
                  width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 10, color: '#f1f5f9', padding: '10px 14px', fontSize: 14, outline: 'none',
                }}>
                  {warehouses.map(w => <option key={w} value={w}>{w}</option>)}
                </select>
              </div>
              <FormField label="New Stock Level (leave empty to keep)" value={form.current_stock} onChange={v => setForm(f => ({...f, current_stock: v}))} type="number" placeholder="0" />
            </>
          )}
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 8 }}>
            <Btn variant="ghost" onClick={() => setModal(null)}>Cancel</Btn>
            <Btn onClick={handleSave} loading={saving}>Save Changes</Btn>
          </div>
        </Modal>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 30, fontWeight: 900, color: '#f1f5f9', letterSpacing: '-0.5px' }}>Inventory Management</h1>
          <p style={{ margin: '6px 0 0', color: '#4b5563', fontSize: 13 }}>{items.length} SKUs tracked across all warehouses</p>
        </div>
        <Btn onClick={openAdd}>+ Add SKU</Btn>
      </div>

      <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search SKUs, names, categories…"
        style={{
          width: '100%', background: 'rgba(30,35,48,0.8)', border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 12, color: '#f1f5f9', padding: '12px 18px', fontSize: 14, outline: 'none',
          boxSizing: 'border-box', marginBottom: 20, transition: 'border-color 0.2s',
        }}
        onFocus={e => e.target.style.borderColor = '#f97316'}
        onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
      />

      <GlassCard style={{ overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'rgba(0,0,0,0.3)' }}>
              {['SKU ID', 'Name', 'Category', 'Total Stock', 'Last Updated', ''].map(h => (
                <th key={h} style={{ padding: '14px 18px', textAlign: 'left', color: '#6b7280', fontSize: 11, fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}><Spinner /> Loading…</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={6}><EmptyState icon="📦" text="No SKUs found" /></td></tr>
            ) : filtered.map((item, i) => (
              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', transition: 'background 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <td style={{ padding: '14px 18px', color: '#f97316', fontWeight: 800, fontSize: 14 }}>{item.sku_id}</td>
                <td style={{ padding: '14px 18px', color: '#f1f5f9', fontSize: 14 }}>{item.name}</td>
                <td style={{ padding: '14px 18px' }}><Badge label={item.category || 'Uncategorized'} color="#374151" /></td>
                <td style={{ padding: '14px 18px', color: item.total_stock < 100 ? '#dc2626' : '#d1d5db', fontWeight: 800, fontSize: 15 }}>{item.total_stock?.toLocaleString()}</td>
                <td style={{ padding: '14px 18px', color: '#6b7280', fontSize: 12 }}>{fmtDate(item.updated_at)}</td>
                <td style={{ padding: '14px 18px' }}>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <Btn small variant="ghost" onClick={() => openEdit(item)}>✏️ Edit</Btn>
                    <Btn small variant="danger" loading={deleting === item.sku_id} onClick={() => handleDelete(item.sku_id)}>🗑</Btn>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </GlassCard>
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
          <h1 style={{ margin: 0, fontSize: 30, fontWeight: 900, color: '#f1f5f9', letterSpacing: '-0.5px' }}>Supplier Management</h1>
          <p style={{ margin: '6px 0 0', color: '#4b5563', fontSize: 13 }}>{suppliers.length} active suppliers</p>
        </div>
        <Btn onClick={openAdd}>+ Add Supplier</Btn>
      </div>

      <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search suppliers, regions…"
        style={{
          width: '100%', background: 'rgba(30,35,48,0.8)', border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 12, color: '#f1f5f9', padding: '12px 18px', fontSize: 14, outline: 'none',
          boxSizing: 'border-box', marginBottom: 20,
        }}
        onFocus={e => e.target.style.borderColor = '#f97316'}
        onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
      />

      <GlassCard style={{ overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'rgba(0,0,0,0.3)' }}>
              {['Supplier', 'Region', 'Lead Time', 'On-Time %', 'Quality', 'Risk Level', ''].map(h => (
                <th key={h} style={{ padding: '14px 18px', textAlign: 'left', color: '#6b7280', fontSize: 11, fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}><Spinner /></td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={7}><EmptyState icon="🏭" text="No suppliers found" /></td></tr>
            ) : filtered.map((s, i) => {
              const risk = s.risk_level || getRiskFromScore(s.risk_score);
              return (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', transition: 'background 0.15s' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                  <td style={{ padding: '14px 18px' }}>
                    <div style={{ fontWeight: 800, color: '#f97316', fontSize: 14 }}>{s.supplier_id}</div>
                    <div style={{ fontSize: 12, color: '#6b7280' }}>{s.name}</div>
                  </td>
                  <td style={{ padding: '14px 18px', color: '#d1d5db', fontSize: 13 }}>{s.region || '—'}</td>
                  <td style={{ padding: '14px 18px', color: '#d1d5db', fontSize: 14, fontWeight: 600 }}>{fmt(s.avg_lead_time_days)} days</td>
                  <td style={{ padding: '14px 18px' }}>
                    <span style={{ color: s.on_time_delivery_pct >= 80 ? '#4ade80' : s.on_time_delivery_pct >= 60 ? '#facc15' : '#f87171', fontWeight: 800, fontSize: 15 }}>
                      {fmt(s.on_time_delivery_pct)}%
                    </span>
                  </td>
                  <td style={{ padding: '14px 18px', color: '#d1d5db', fontSize: 14 }}>{fmt(s.quality_score)}/10</td>
                  <td style={{ padding: '14px 18px' }}>
                    <Badge label={risk.toUpperCase()} color={getRiskColor(risk)} />
                  </td>
                  <td style={{ padding: '14px 18px' }}>
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
      </GlassCard>
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
        <h1 style={{ margin: 0, fontSize: 30, fontWeight: 900, color: '#f1f5f9', letterSpacing: '-0.5px' }}>Action History</h1>
        <p style={{ margin: '6px 0 0', color: '#4b5563', fontSize: 13 }}>Full audit log of all agent-proposed and manually triggered actions</p>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {STATUS_FILTERS.map(s => (
          <button key={s} onClick={() => setFilter(s)} style={{
            padding: '8px 18px', borderRadius: 10, border: 'none', cursor: 'pointer',
            fontSize: 13, fontWeight: 700,
            background: filter === s ? 'linear-gradient(135deg, #f97316, #ea580c)' : 'rgba(255,255,255,0.06)',
            color: filter === s ? '#fff' : '#6b7280',
            boxShadow: filter === s ? '0 4px 12px rgba(249,115,22,0.3)' : 'none',
            transition: 'all 0.2s',
          }}>
            {s === 'all' ? 'All' : s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
            {' '}<span style={{ opacity: 0.7 }}>({counts[s]})</span>
          </button>
        ))}
      </div>

      <GlassCard style={{ overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'rgba(0,0,0,0.3)' }}>
              {['Type', 'Details', 'Reasoning', 'Status', 'Created', 'Updated'].map(h => (
                <th key={h} style={{ padding: '14px 18px', textAlign: 'left', color: '#6b7280', fontSize: 11, fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}><Spinner /></td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={6}><EmptyState icon="📋" text="No actions found" /></td></tr>
            ) : filtered.map((a, i) => (
              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', transition: 'background 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <td style={{ padding: '14px 18px' }}>
                  <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 13 }}>
                    {a.action_type === 'reorder' ? '📦 Reorder' : '🔄 Switch Supplier'}
                  </span>
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <div style={{ fontSize: 12, color: '#9ca3af' }}>
                    {Object.entries(a.details || {}).map(([k, v]) => (
                      <div key={k}><span style={{ color: '#6b7280' }}>{k}:</span> <strong style={{ color: '#d1d5db' }}>{String(v)}</strong></div>
                    ))}
                  </div>
                </td>
                <td style={{ padding: '14px 18px', fontSize: 12, color: '#6b7280', maxWidth: 200, fontStyle: 'italic' }}>{a.reasoning || '—'}</td>
                <td style={{ padding: '14px 18px' }}>
                  <Badge label={a.status?.replace(/_/g,' ').toUpperCase()} color={getStatusColor(a.status)} />
                </td>
                <td style={{ padding: '14px 18px', fontSize: 12, color: '#6b7280', whiteSpace: 'nowrap' }}>{fmtDate(a.created_at)}</td>
                <td style={{ padding: '14px 18px', fontSize: 12, color: '#6b7280', whiteSpace: 'nowrap' }}>{fmtDate(a.updated_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </GlassCard>
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
    <div style={{
      display: 'flex', minHeight: '100vh',
      background: 'radial-gradient(ellipse at 20% 50%, rgba(124,58,237,0.06) 0%, transparent 50%), radial-gradient(ellipse at 80% 20%, rgba(249,115,22,0.05) 0%, transparent 50%), #0a0d16',
      fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
      color: '#f1f5f9',
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        * { box-sizing: border-box; }
        body { margin: 0; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes subtlePulse { 0%,100% { opacity: 1; box-shadow: 0 0 0 0 currentColor; } 50% { opacity: 0.8; box-shadow: 0 0 0 4px transparent; } }
        @keyframes criticalPulse { 0%,100% { box-shadow: 0 0 0 0 rgba(220,38,38,0); } 50% { box-shadow: 0 0 0 4px rgba(220,38,38,0.15); } }
        @keyframes slideUp { from { transform: translateY(16px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes modalIn { from { transform: scale(0.96); opacity: 0; } to { transform: scale(1); opacity: 1; } }
        @keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.18); }
        input[type="range"] { -webkit-appearance: none; appearance: none; height: 6px; border-radius: 3px; background: rgba(255,255,255,0.1); outline: none; }
        input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 18px; height: 18px; border-radius: 50%; background: linear-gradient(135deg,#7c3aed,#6d28d9); cursor: pointer; box-shadow: 0 2px 8px rgba(124,58,237,0.5); }
        select option { background: #1a1f2e; }
      `}</style>

      <Sidebar active={page} onNav={setPage} />

      <main style={{ flex: 1, overflowY: 'auto', padding: '36px 40px', maxWidth: 1400 }}>
        {pages[page]}
      </main>
    </div>
  );
}
