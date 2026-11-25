import { useCallback, useEffect, useState } from 'react'
import { api, API_URL } from './api'
import PredictForm from './components/PredictForm'
import History from './components/History'
import Metrics from './components/Metrics'
import DataPanel from './components/DataPanel'

const TABS = [
  { id: 'predict', label: '🌱 Predecir' },
  { id: 'history', label: '🕘 Historial' },
  { id: 'metrics', label: '📊 Métricas' },
  { id: 'data', label: '🗂 Datos y re-entrenamiento' },
]

export default function App() {
  const [tab, setTabState] = useState(() => {
    const h = window.location.hash.slice(1)
    return TABS.some((t) => t.id === h) ? h : 'predict'
  })
  const setTab = (id) => { setTabState(id); window.history.replaceState(null, '', `#${id}`) }
  const [health, setHealth] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const refresh = useCallback(() => setRefreshKey((k) => k + 1), [])

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ status: 'down' }))
  }, [refreshKey])

  const statusClass = health?.status === 'ok' ? 'good' : health?.status === 'degraded' ? 'warn' : 'bad'
  const statusText = !health ? 'Conectando…'
    : health.status === 'ok' ? `Servicio activo · modelo v${health.active_model_version}`
      : health.status === 'degraded' ? 'Servicio degradado' : 'API no disponible'

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Recomendador de Cultivos IA</h1>
          <p className="muted">Clasificación de 22 cultivos según el suelo y el clima · CRISP-ML(Q)</p>
        </div>
        <div className="status">
          <span className={`badge ${statusClass}`}>● {statusText}</span>
          <a className="muted small" href={API_URL.replace(/\/api$/, '/docs')} target="_blank" rel="noreferrer">Swagger ↗</a>
        </div>
      </header>
      <nav className="tabs" role="tablist">
        {TABS.map((t) => (
          <button key={t.id} role="tab" aria-selected={tab === t.id} className={tab === t.id ? 'active' : ''} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>
      <main>
        {tab === 'predict' && <PredictForm onPredicted={refresh} />}
        {tab === 'history' && <History refreshKey={refreshKey} />}
        {tab === 'metrics' && <Metrics refreshKey={refreshKey} onChanged={refresh} />}
        {tab === 'data' && <DataPanel refreshKey={refreshKey} onChanged={refresh} />}
      </main>
    </div>
  )
}
