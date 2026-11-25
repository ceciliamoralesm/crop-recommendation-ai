import { useEffect, useState } from 'react'
import { api, cropName, fmtDate, pct } from '../api'
import { BarList, ConfusionMatrix } from './charts'

export default function Metrics({ refreshKey, onChanged }) {
  const [models, setModels] = useState([])
  const [version, setVersion] = useState(null)
  const [m, setM] = useState(null)
  const [error, setError] = useState('')
  const [showTable, setShowTable] = useState(false)

  useEffect(() => {
    api.models().then((list) => {
      setModels(list)
      setVersion(list.find((x) => x.is_active)?.version ?? list[0]?.version ?? null)
    }).catch((e) => setError(e.message))
  }, [refreshKey])

  useEffect(() => {
    if (version != null) api.metrics(version).then(setM).catch((e) => setError(e.message))
  }, [version, refreshKey])

  const activate = async () => {
    try {
      await api.activate(version)
      onChanged?.()
    } catch (e) {
      setError(e.message)
    }
  }

  if (error) return <p className="alert error">{error}</p>
  if (!m) return <p className="muted">Cargando métricas…</p>

  const perClass = Object.entries(m.per_class)
    .map(([label, v]) => ({ label, display: cropName(label), value: v.f1 }))
    .sort((a, b) => a.value - b.value)
  const f1Min = Math.max(0, Math.floor((Math.min(...perClass.map((p) => p.value)) - 0.05) * 20) / 20)
  const importances = Object.entries(m.hyperparams?.feature_importances ?? {})
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value)

  return (
    <div className="stack">
      <div className="card card-head">
        <div>
          <h2>Métricas del modelo</h2>
          <p className="muted">{m.algorithm} · entrenado {fmtDate(m.trained_at)} · {m.n_train} muestras de entrenamiento y {m.n_test} de prueba</p>
        </div>
        <div className="inline">
          <label>Versión:{' '}
            <select value={version ?? ''} onChange={(e) => setVersion(Number(e.target.value))}>
              {models.map((x) => <option key={x.version} value={x.version}>v{x.version}{x.is_active ? ' (activa)' : ''}</option>)}
            </select>
          </label>
          {!m.is_active && <button className="btn" onClick={activate}>Activar esta versión</button>}
          {m.is_active && <span className="badge good">✓ Activa</span>}
        </div>
      </div>

      <div className="tiles">
        {[
          ['Accuracy', m.accuracy], ['Precision (macro)', m.precision_macro],
          ['Recall (macro)', m.recall_macro], ['F1 (macro)', m.f1_macro],
        ].map(([k, v]) => (
          <div className="tile" key={k}><span className="tile-label">{k}</span><span className="tile-value">{pct(v, 2)}</span></div>
        ))}
        <div className="tile">
          <span className="tile-label">F1 validación cruzada</span>
          <span className="tile-value">{pct(m.cv_f1_mean, 2)}</span>
          <span className="tile-sub">± {pct(m.cv_f1_std, 2)} (5 folds)</span>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>F1 por cultivo (de menor a mayor)</h3>
          <BarList items={perClass} max={1} domainMin={f1Min} format={(v) => v.toFixed(3)} />
          <p className="muted small">El eje empieza en {f1Min.toFixed(2)} (no en 0) para que se vean las diferencias.</p>
        </div>
        <div className="card">
          <h3>Importancia de variables</h3>
          <BarList items={importances} format={(v) => pct(v)} />
          <p className="muted small">Cuánto contribuye cada variable a las decisiones del Random Forest.</p>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>Matriz de confusión (conjunto de prueba)</h3>
          <button className="btn small" onClick={() => setShowTable(!showTable)}>{showTable ? 'Ver matriz' : 'Ver tabla por clase'}</button>
        </div>
        {!showTable ? (
          <ConfusionMatrix classes={m.classes} matrix={m.confusion_matrix} nameOf={cropName} />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead><tr><th>Cultivo</th><th className="num">Precision</th><th className="num">Recall</th><th className="num">F1</th><th className="num">Soporte</th></tr></thead>
              <tbody>
                {Object.entries(m.per_class).map(([c, v]) => (
                  <tr key={c}><td>{cropName(c)}</td><td className="num">{v.precision.toFixed(3)}</td><td className="num">{v.recall.toFixed(3)}</td><td className="num">{v.f1.toFixed(3)}</td><td className="num">{v.support}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
