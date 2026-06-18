import { useState, useEffect, useRef, useCallback } from 'react'

interface Message {
  id: string
  role: 'user' | 'agent' | 'log'
  text: string
  logs?: string
  images?: { path: string; rel: string }[]
  ts: string
  status?: 'ok' | 'err' | 'running'
}

interface Moodboard { name: string; path: string; count: number }

/* ── Title bar ── */
function TitleBar() {
  const ctrl = (a: string) => window.layershot?.windowControl(a)
  return (
    <div className="titlebar">
      <div className="tb-brand">
        <div className="ls-logo">
          <div className="ls-top">LA<span className="ls-accent">Y</span>ERSHOT</div>
          <div className="ls-bot">PACKSHOT · STUDIO</div>
        </div>
      </div>
      <div className="tb-status">
        <div className="tb-dot" />
        LAYERSHOT · AGENT ACTIF
      </div>
      <div className="tb-controls">
        <button className="ctrl" onClick={() => ctrl('minimize')}>—</button>
        <button className="ctrl" onClick={() => ctrl('maximize')}>⊡</button>
        <button className="ctrl close" onClick={() => ctrl('close')}>✕</button>
      </div>
    </div>
  )
}

/* ── Status bar ── */
function StatusBar({ running, moodboardName }: { running: boolean; moodboardName: string }) {
  const [time, setTime] = useState(new Date())
  const [mlxOk, setMlxOk] = useState<boolean | null>(null)
  const [sdxlOk, setSdxlOk] = useState<boolean | null>(null)

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    window.layershot?.health().then(h => {
      setMlxOk(h.project)
      setSdxlOk(h.moodboards && h.outputs)
    }).catch(() => { setMlxOk(false); setSdxlOk(false) })
  }, [])

  const pad = (n: number) => String(n).padStart(2, '0')
  return (
    <div className="status-bar">
      <div className="status-item">
        <span className="status-label">HEURE</span>
        <span className="status-val">{pad(time.getHours())}:{pad(time.getMinutes())}:{pad(time.getSeconds())}</span>
      </div>
      <div className="status-sep" />
      <div className="status-item">
        <span className={`status-dot ${mlxOk ? 'ok' : 'err'}`} />
        <span className="status-label">MLX</span>
        <span className={`status-val ${mlxOk ? '' : 'err-text'}`}>{mlxOk ? 'OK' : 'OFF'}</span>
      </div>
      <div className="status-sep" />
      <div className="status-item">
        <span className={`status-dot ${sdxlOk ? 'ok' : 'err'}`} />
        <span className="status-label">SDXL</span>
        <span className={`status-val ${sdxlOk ? '' : 'err-text'}`}>{sdxlOk ? 'OK' : 'OFF'}</span>
      </div>
      <div className="status-sep" />
      <div className="status-item">
        <span className={`status-dot ${running ? 'warn' : 'ok'}`} />
        <span className="status-label">PIPELINE</span>
        <span className="status-val">{running ? 'RUN' : 'IDLE'}</span>
      </div>
      <div className="status-sep" />
      <div className="status-item">
        <span className="status-label">MOODBOARD</span>
        <span className="status-val">{moodboardName.toUpperCase()}</span>
      </div>
    </div>
  )
}

/* ── Log block with auto-scroll ── */
function LogBlock({ logs }: { logs: string }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight }, [logs])
  return <div className="log-block" ref={ref}>{logs}</div>
}

/* ── Main App ── */
export default function App() {
  const [messages, setMessages] = useState<Message[]>([{
    id: 'welcome',
    role: 'agent',
    text: 'Bonjour. Je suis LayerShot. Donne-moi un produit et une couleur, ex. "parfum de luxe : gold". Je lance le pipeline SDXL + rembg sur le moodboard studio.',
    ts: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
  }])
  const [input, setInput] = useState('')
  const [moodboards, setMoodboards] = useState<Moodboard[]>([])
  const [selectedMoodboard, setSelectedMoodboard] = useState<string>('studio')
  const [renderMode, setRenderMode] = useState<'isolated' | 'white_background' | 'enhanced'>('white_background')
  const [backend, setBackend] = useState<'mlx' | 'claude' | 'ollama'>('mlx')
  const [loading, setLoading] = useState(false)
  const [runningMsgId, setRunningMsgId] = useState<string | null>(null)
  const feedRef = useRef<HTMLDivElement>(null)

  /* Auto-scroll */
  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight
  }, [messages, loading])

  /* Load moodboards */
  useEffect(() => {
    window.layershot?.listMoodboards().then(mbs => {
      setMoodboards(mbs)
      if (mbs.length && !mbs.find(m => m.name === selectedMoodboard)) {
        setSelectedMoodboard(mbs[0].name)
      }
    })
  }, [])

  /* Subscribe to pipeline events */
  useEffect(() => {
    const offLog = window.layershot?.onLog((chunk) => {
      setMessages(prev => {
        const idx = prev.findIndex(m => m.id === runningMsgId)
        if (idx < 0) return prev
        const copy = [...prev]
        copy[idx] = { ...copy[idx], logs: (copy[idx].logs || '') + chunk }
        return copy
      })
    })
    const offDone = window.layershot?.onDone(async ({ code }) => {
      const outs = await window.layershot!.listOutputs()
      const recent = outs.slice(0, 12)
      setMessages(prev => {
        const idx = prev.findIndex(m => m.id === runningMsgId)
        if (idx < 0) return prev
        const copy = [...prev]
        copy[idx] = {
          ...copy[idx],
          status: code === 0 ? 'ok' : 'err',
          text: code === 0
            ? `Pipeline terminé. ${recent.length} images récentes affichées ci-dessous.`
            : `Pipeline échoué (exit ${code}). Voir les logs ci-dessous.`,
          images: recent.map(r => ({ path: r.path, rel: r.rel })),
        }
        return copy
      })
      setLoading(false)
      setRunningMsgId(null)
    })
    return () => { offLog?.(); offDone?.() }
  }, [runningMsgId])

  /* Submit — parse "product : color" or "product:color" */
  const sendMessage = useCallback(async () => {
    const raw = input.trim()
    if (!raw || loading) return
    setInput('')

    // Parse products — split by comma or newline, normalize "X : Y" → "X:Y"
    const products = raw.split(/[,\n]/).map(p => p.trim().replace(/\s*:\s*/, ':')).filter(Boolean)
    if (!products.length || !products.every(p => p.includes(':'))) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'agent',
        text: 'Format attendu : "nom-produit : couleur" (sépare par virgule pour plusieurs).',
        ts: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        status: 'err',
      }])
      return
    }

    const ts = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    const userId = `u-${Date.now()}`
    const agentId = `a-${Date.now()}`
    setMessages(prev => [
      ...prev,
      { id: userId, role: 'user', text: raw, ts },
      { id: agentId, role: 'agent', text: 'Pipeline en cours…', ts, status: 'running', logs: '' },
    ])

    const mb = moodboards.find(m => m.name === selectedMoodboard)
    if (!mb) return

    setLoading(true)
    setRunningMsgId(agentId)
    const res = await window.layershot!.runPipeline({
      moodboard: mb.path,
      products,
      session: `ui-${Date.now()}`,
      renderMode,
      backend,
    })
    if (!res.ok) {
      setMessages(prev => prev.map(m => m.id === agentId
        ? { ...m, text: `Erreur: ${res.error}`, status: 'err' } : m))
      setLoading(false)
      setRunningMsgId(null)
    }
  }, [input, loading, moodboards, selectedMoodboard, renderMode, backend])

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  const stopPipeline = async () => {
    await window.layershot?.stopPipeline()
    setLoading(false)
    setRunningMsgId(null)
  }

  return (
    <>
      <TitleBar />
      <div className="app-body">
        <div className="center-panel">
          {/* Config row */}
          <div className="config-row">
            <div className="config-chip">
              <span>Moodboard</span>
              <select
                className="model-selector"
                style={{ minWidth: 140, padding: '4px 8px', fontSize: 11 }}
                value={selectedMoodboard}
                onChange={e => setSelectedMoodboard(e.target.value)}
                disabled={loading}
              >
                {moodboards.map(m => (
                  <option key={m.name} value={m.name}>
                    {m.name} ({m.count})
                  </option>
                ))}
              </select>
            </div>
            <div className="config-chip">
              <span>Mode</span>
              <select
                className="model-selector"
                style={{ minWidth: 130, padding: '4px 8px', fontSize: 11 }}
                value={renderMode}
                onChange={e => setRenderMode(e.target.value as any)}
                disabled={loading}
              >
                <option value="isolated">Isolé</option>
                <option value="white_background">Fond blanc</option>
                <option value="enhanced">Enhanced</option>
              </select>
            </div>
            <div className="config-chip">
              <span>Backend IA</span>
              <select
                className="model-selector"
                style={{ minWidth: 110, padding: '4px 8px', fontSize: 11 }}
                value={backend}
                onChange={e => setBackend(e.target.value as any)}
                disabled={loading}
              >
                <option value="mlx">MLX</option>
                <option value="claude">Claude</option>
                <option value="ollama">Ollama</option>
              </select>
            </div>
          </div>

          {/* Chat feed */}
          <div className="feed" ref={feedRef}>
            {messages.map(msg => (
              <div key={msg.id} className={`msg ${msg.role === 'user' ? 'msg-user' : 'msg-agent'}`}>
                <div className="msg-header">
                  <span>{msg.role === 'user' ? 'Vous' : 'LayerShot'}</span>
                  {msg.status === 'err' && <span className="badge badge-err">Erreur</span>}
                  {msg.status === 'running' && <span className="badge badge-sdxl">SDXL</span>}
                  <span className="msg-ts">{msg.ts}</span>
                </div>
                <div className="msg-body">{msg.text}</div>
                {msg.images && msg.images.length > 0 && (
                  <div className="img-grid">
                    {msg.images.map((img, i) => (
                      <img key={i} src={`file://${img.path}`} alt={img.rel} title={img.rel} />
                    ))}
                  </div>
                )}
                {msg.logs && <LogBlock logs={msg.logs} />}
              </div>
            ))}
            {loading && !messages.find(m => m.id === runningMsgId)?.logs && (
              <div className="msg msg-agent">
                <div className="msg-header"><span>LayerShot</span></div>
                <div className="typing-indicator"><span /><span /><span /></div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="input-area">
            <div className="input-row">
              <textarea
                className="chat-textarea"
                placeholder='Ex: parfum-luxe : gold, sac-cuir : matte-black'
                value={input}
                onChange={e => {
                  setInput(e.target.value)
                  e.target.style.height = 'auto'
                  e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px'
                }}
                onKeyDown={onKey}
                disabled={loading}
                rows={1}
              />
              {loading ? (
                <button className="icon-btn stop-btn" onClick={stopPipeline} title="Stop">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="1"/></svg>
                </button>
              ) : (
                <button className="icon-btn send-btn" onClick={sendMessage} disabled={!input.trim()} title="Envoyer">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="22" y1="2" x2="11" y2="13"/>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                  </svg>
                </button>
              )}
            </div>
          </div>

          <StatusBar running={loading} moodboardName={selectedMoodboard} />
        </div>
      </div>
    </>
  )
}
