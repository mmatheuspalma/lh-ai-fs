import { useState } from 'react'

const VERDICT_COLORS = {
  supports: '#1a7f37', accurate: '#1a7f37', corroborated: '#1a7f37',
  overstates: '#bf8700', overstated: '#bf8700', altered: '#bf8700',
  misattributed: '#cf222e', likely_fabricated: '#cf222e',
  wrong_jurisdiction: '#cf222e', contradicted: '#cf222e',
  could_not_verify: '#6e7781', unverifiable: '#6e7781',
}
const SEV_COLORS = { high: '#cf222e', medium: '#bf8700', low: '#6e7781' }

function Badge({ text, color }) {
  return (
    <span style={{
      background: color, color: 'white', borderRadius: '10px',
      padding: '2px 10px', fontSize: '12px', fontWeight: 600,
      textTransform: 'capitalize', whiteSpace: 'nowrap',
    }}>{String(text).replace(/_/g, ' ')}</span>
  )
}

function Confidence({ value }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '140px' }}>
      <div style={{ flex: 1, height: '6px', background: '#eaeef2', borderRadius: '3px' }}>
        <div style={{
          width: `${Math.round(value * 100)}%`, height: '100%',
          background: '#0969da', borderRadius: '3px',
        }} />
      </div>
      <span style={{ fontSize: '12px', color: '#57606a' }}>{Math.round(value * 100)}%</span>
    </div>
  )
}

function Finding({ title, verdict, severity, confidence, reasoning, explanation, evidence, defaultOpen }) {
  const [open, setOpen] = useState(!!defaultOpen)
  return (
    <div style={{ border: '1px solid #d0d7de', borderRadius: '8px', padding: '14px', marginBottom: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'flex-start' }}>
        <div style={{ fontWeight: 600, flex: 1 }}>{title}</div>
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          <Badge text={verdict} color={VERDICT_COLORS[verdict] || '#6e7781'} />
          {severity && <Badge text={severity} color={SEV_COLORS[severity] || '#6e7781'} />}
        </div>
      </div>
      <div style={{ marginTop: '8px' }}><Confidence value={confidence ?? 0} /></div>
      <p style={{ margin: '10px 0 0', color: '#24292f' }}>{explanation}</p>
      {evidence && evidence.length > 0 && (
        <div style={{ marginTop: '8px' }}>
          {evidence.map((e, i) => (
            <div key={i} style={{ fontSize: '13px', background: '#f6f8fa', borderLeft: '3px solid #cf222e',
              padding: '6px 10px', margin: '4px 0', borderRadius: '0 4px 4px 0' }}>
              <strong>{e.doc}:</strong> "{e.excerpt}"
            </div>
          ))}
        </div>
      )}
      {reasoning && (
        <>
          <button onClick={() => setOpen(!open)} style={{
            marginTop: '8px', background: 'none', border: 'none', color: '#0969da',
            cursor: 'pointer', padding: 0, fontSize: '13px' }}>
            {open ? '▾ hide confidence reasoning' : '▸ why this confidence?'}
          </button>
          {open && <p style={{ margin: '6px 0 0', fontSize: '13px', color: '#57606a' }}>{reasoning}</p>}
        </>
      )}
    </div>
  )
}

function Section({ title, count, children }) {
  return (
    <div style={{ marginTop: '28px' }}>
      <h2 style={{ fontSize: '18px', borderBottom: '2px solid #d0d7de', paddingBottom: '6px' }}>
        {title} <span style={{ color: '#57606a', fontWeight: 400 }}>({count})</span>
      </h2>
      {count === 0
        ? <p style={{ color: '#6e7781' }}>No findings.</p>
        : children}
    </div>
  )
}

function App() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const runAnalysis = async () => {
    setLoading(true); setError(null); setReport(null)
    try {
      const res = await fetch('http://localhost:8002/analyze', { method: 'POST' })
      if (!res.ok) throw new Error(`Server responded with ${res.status}`)
      const data = await res.json()
      setReport(data.report)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const s = report?.summary
  const degraded = report && Object.values(report.pipeline_status?.agents || {}).some(v => v !== 'ok')

  return (
    <div style={{ maxWidth: '860px', margin: '40px auto', padding: '0 20px',
      fontFamily: 'system-ui, sans-serif', color: '#24292f' }}>
      <h1>BS Detector</h1>
      <p style={{ color: '#57606a' }}>Legal brief verification pipeline — <em>Rivera v. Harmon Construction Group</em></p>

      <button onClick={runAnalysis} disabled={loading} style={{
        padding: '10px 24px', fontSize: '16px', borderRadius: '6px',
        border: '1px solid #1a7f37', background: loading ? '#94d3a2' : '#1a7f37',
        color: 'white', cursor: loading ? 'not-allowed' : 'pointer' }}>
        {loading ? 'Analyzing…' : 'Run Analysis'}
      </button>

      {error && <div style={{ marginTop: '20px', color: '#cf222e' }}><strong>Error:</strong> {error}</div>}
      {!report && !loading && !error && (
        <p style={{ marginTop: '20px', color: '#888' }}>Click "Run Analysis" to analyze the case documents.</p>
      )}

      {report && (
        <div style={{ marginTop: '24px' }}>
          {degraded && (
            <div style={{ background: '#fff8c5', border: '1px solid #d4a72c', borderRadius: '6px',
              padding: '10px 14px', marginBottom: '16px' }}>
              ⚠ Some agents degraded: {JSON.stringify(report.pipeline_status.agents)}
            </div>
          )}

          <div style={{ background: '#0d1117', color: '#e6edf3', borderRadius: '8px', padding: '18px' }}>
            <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px',
              color: '#7d8590' }}>Judicial Memo</div>
            <p style={{ margin: '8px 0 0', lineHeight: 1.55 }}>{report.judicial_memo}</p>
          </div>

          <div style={{ display: 'flex', gap: '12px', marginTop: '18px', flexWrap: 'wrap' }}>
            <Stat label="Total flags" value={s.total_flags} />
            <Stat label="High severity" value={s.by_severity?.high || 0} color="#cf222e" />
            <Stat label="Citations flagged" value={s.by_category?.citation || 0} />
            <Stat label="Quotes flagged" value={s.by_category?.quote || 0} />
            <Stat label="Fact conflicts" value={s.by_category?.fact || 0} />
          </div>

          <Section title="Citation Verification" count={report.citations.length}>
            {report.citations.map((c) => (
              <Finding key={c.citation_id} title={c.case_name} verdict={c.verdict}
                severity={c.severity} confidence={c.confidence} explanation={c.explanation}
                reasoning={c.confidence_reasoning} defaultOpen={false} />
            ))}
          </Section>

          <Section title="Quote Accuracy" count={report.quotes.length}>
            {report.quotes.map((q) => (
              <Finding key={q.quote_id} title={`"${q.quoted_text}"`} verdict={q.verdict}
                severity={q.severity} confidence={q.confidence} explanation={q.explanation}
                reasoning={q.confidence_reasoning} />
            ))}
          </Section>

          <Section title="Cross-Document Consistency" count={report.cross_document.length}>
            {report.cross_document.map((f, i) => (
              <Finding key={i} title={f.claim} verdict={f.status} severity={f.severity}
                confidence={f.confidence} explanation={f.explanation}
                reasoning={f.confidence_reasoning} evidence={f.evidence} />
            ))}
          </Section>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value, color }) {
  return (
    <div style={{ border: '1px solid #d0d7de', borderRadius: '8px', padding: '12px 16px', minWidth: '120px' }}>
      <div style={{ fontSize: '24px', fontWeight: 700, color: color || '#24292f' }}>{value}</div>
      <div style={{ fontSize: '12px', color: '#57606a' }}>{label}</div>
    </div>
  )
}

export default App
