import { useEffect, useState } from 'react'
import { api, CROP_ES, cropName, FIELDS, fmtDate, pct } from '../api'

export default function History({ refreshKey }) {
  const [data, setData] = useState(null)
  const [page, setPage] = useState(1)
  const [label, setLabel] = useState('')
  const [error, setError] = useState('')
  const size = 10

  useEffect(() => {
    api.predictions({ page, size, label }).then(setData).catch((e) => setError(e.message))
  }, [page, label, refreshKey])

  const pages = data ? Math.max(1, Math.ceil(data.total / size)) : 1

  return (
    <div className="card">
      <div className="card-head">
        <h2>Historial de predicciones</h2>
        <label className="inline">
          Filtrar por cultivo:{' '}
          <select value={label} onChange={(e) => { setLabel(e.target.value); setPage(1) }}>
            <option value="">Todos</option>
            {Object.keys(CROP_ES).sort().map((c) => <option key={c} value={c}>{cropName(c)}</option>)}
          </select>
        </label>
      </div>
      {error && <p className="alert error">{error}</p>}
      {data && (
        <>
          <p className="muted">{data.total} predicciones registradas</p>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>#</th><th>Fecha</th>
                  {FIELDS.map((f) => <th key={f.key} className="num">{f.key}</th>)}
                  <th>Resultado</th><th className="num">Confianza</th><th className="num">Modelo</th>
                </tr>
              </thead>
              <tbody>
                {data.items.length === 0 && (
                  <tr><td colSpan={FIELDS.length + 5} className="muted center">Sin predicciones todavía</td></tr>
                )}
                {data.items.map((p) => (
                  <tr key={p.id}>
                    <td>{p.id}</td>
                    <td className="nowrap">{fmtDate(p.created_at)}</td>
                    {FIELDS.map((f) => <td key={f.key} className="num">{+p.input[f.key].toFixed(2)}</td>)}
                    <td><strong>{cropName(p.predicted_label)}</strong></td>
                    <td className="num">{pct(p.confidence)}</td>
                    <td className="num">v{p.model_version}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pager">
            <button className="btn" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Anterior</button>
            <span>Página {page} de {pages}</span>
            <button className="btn" disabled={page >= pages} onClick={() => setPage(page + 1)}>Siguiente →</button>
          </div>
        </>
      )}
    </div>
  )
}
