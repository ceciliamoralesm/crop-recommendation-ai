import { useEffect, useState } from 'react'
import { api, cropName, fmtDate, pct } from '../api'
import { BarList } from './charts'

function RetrainResult({ r }) {
  return (
    <div className={`alert ${r.activated ? 'good' : 'warn'}`}>
      <strong>{r.activated ? '✓ Nuevo modelo activado' : '⚠ Nuevo modelo NO activado'}: v{r.new_version}</strong>
      {r.previous_version && <> (antes v{r.previous_version}, F1 {pct(r.previous_f1_macro, 2)})</>}
      <br />F1 macro nuevo: {pct(r.metrics.f1_macro, 2)} · Accuracy: {pct(r.metrics.accuracy, 2)}
      <br /><span className="small">{r.reason}</span>
    </div>
  )
}

export default function DataPanel({ refreshKey, onChanged }) {
  const [info, setInfo] = useState(null)
  const [file, setFile] = useState(null)
  const [mode, setMode] = useState('append')
  const [autoRetrain, setAutoRetrain] = useState(true)
  const [busy, setBusy] = useState('')
  const [upload, setUpload] = useState(null)
  const [retrain, setRetrain] = useState(null)
  const [error, setError] = useState('')

  const load = () => api.datasets().then(setInfo).catch((e) => setError(e.message))
  useEffect(() => { load() }, [refreshKey])

  const run = async (kind, fn) => {
    setBusy(kind); setError('')
    try { await fn(); await load(); onChanged?.() } catch (e) { setError(e.message) } finally { setBusy('') }
  }

  const doUpload = (e) => {
    e.preventDefault()
    if (!file) return
    run('upload', async () => {
      const r = await api.upload(file, mode, autoRetrain)
      setUpload(r)
      setRetrain(r.retrain)
    })
  }

  const doRetrain = (force) => run('retrain', async () => { setUpload(null); setRetrain(await api.retrain(force)) })

  return (
    <div className="stack">
      <div className="grid-2">
        <form className="card" onSubmit={doUpload}>
          <h2>Subir archivo de entrenamiento</h2>
          <p className="muted">CSV con columnas <code>N,P,K,temperature,humidity,ph,rainfall,label</code>.{' '}
            <a href={api.templateUrl}>Descargar plantilla</a></p>
          <label className="dropzone">
            <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files[0] ?? null)} />
            <span>{file ? `📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)` : 'Haz clic para elegir un archivo .csv'}</span>
          </label>
          <fieldset className="radios">
            <legend>Modo de carga</legend>
            <label><input type="radio" checked={mode === 'append'} onChange={() => setMode('append')} /> Añadir a los datos actuales</label>
            <label><input type="radio" checked={mode === 'replace'} onChange={() => setMode('replace')} /> Reemplazar los datos activos</label>
          </fieldset>
          <label><input type="checkbox" checked={autoRetrain} onChange={(e) => setAutoRetrain(e.target.checked)} /> Re-entrenar automáticamente tras la carga</label>
          <button className="btn primary" disabled={!file || busy}>{busy === 'upload' ? 'Subiendo…' : 'Subir CSV'}</button>
          {upload && (
            <div className="alert good">
              <strong>✓ Dataset “{upload.dataset.filename}” cargado</strong> ({upload.mode === 'append' ? 'añadido' : 'reemplazo'})<br />
              Filas: {upload.validation.total_rows} totales, {upload.validation.valid_rows} válidas ·
              rechazadas: {upload.validation.rejected_null_or_non_numeric} nulas o no numéricas, {upload.validation.rejected_out_of_range} fuera de rango ·
              duplicadas eliminadas: {upload.validation.duplicates_removed}<br />
              Total de muestras activas: {upload.total_active_samples}
            </div>
          )}
        </form>

        <div className="card">
          <h2>Re-entrenar el modelo</h2>
          <p className="muted">
            Entrena una nueva versión con <strong>todos los datasets activos</strong>. El nuevo modelo solo se activa
            si su F1 no empeora más de un 1 % respecto al actual (control de calidad CRISP-ML(Q)).
          </p>
          <div className="row">
            <button className="btn primary" disabled={!!busy} onClick={() => doRetrain(false)}>
              {busy === 'retrain' ? 'Entrenando…' : 'Re-entrenar'}
            </button>
            <button className="btn" disabled={!!busy} onClick={() => doRetrain(true)}>Re-entrenar y forzar la activación</button>
          </div>
          {busy && <p className="muted">Procesando: entrenamiento con validación cruzada de 5 folds…</p>}
          {retrain && <RetrainResult r={retrain} />}
          {error && <p className="alert error">{error}</p>}
        </div>
      </div>

      {info && (
        <div className="grid-2">
          <div className="card">
            <h3>Datasets cargados</h3>
            <div className="table-wrap">
              <table className="data">
                <thead><tr><th>#</th><th>Archivo</th><th>Fecha</th><th className="num">Filas</th><th>Activo</th></tr></thead>
                <tbody>
                  {info.datasets.map((d) => (
                    <tr key={d.id}>
                      <td>{d.id}</td><td>{d.filename}</td><td className="nowrap">{fmtDate(d.uploaded_at)}</td>
                      <td className="num">{d.n_rows}</td>
                      <td>
                        <input type="checkbox" checked={d.is_active} aria-label={`Activar dataset ${d.filename}`}
                          onChange={(e) => run('toggle', () => api.toggleDataset(d.id, e.target.checked))} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="muted small">Los cambios de activación se aplican en el próximo re-entrenamiento.</p>
          </div>
          <div className="card">
            <h3>Muestras activas por cultivo ({info.total_active_samples} en total)</h3>
            <BarList items={Object.entries(info.class_distribution).map(([label, value]) => ({ label, display: cropName(label), value }))} />
          </div>
        </div>
      )}
    </div>
  )
}
