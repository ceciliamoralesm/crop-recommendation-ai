import { useState } from 'react'
import { api, cropName, FIELDS, pct } from '../api'
import { BarList } from './charts'

const EXAMPLES = {
  'Arroz': { N: 90, P: 42, K: 43, temperature: 20.88, humidity: 82, ph: 6.5, rainfall: 202.9 },
  'Café': { N: 101, P: 31, K: 26, temperature: 26.5, humidity: 57.4, ph: 6.7, rainfall: 155.6 },
  'Manzana': { N: 24, P: 128, K: 196, temperature: 22.8, humidity: 90.7, ph: 5.5, rainfall: 110.4 },
  'Garbanzo': { N: 40, P: 72, K: 77, temperature: 17.0, humidity: 16.9, ph: 7.5, rainfall: 88.6 },
}

export default function PredictForm({ onPredicted }) {
  const [values, setValues] = useState(EXAMPLES['Arroz'])
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const payload = Object.fromEntries(FIELDS.map((f) => [f.key, Number(values[f.key])]))
      const r = await api.predict(payload)
      setResult(r)
      onPredicted?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid-2">
      <form className="card" onSubmit={submit}>
        <h2>Condiciones de la parcela</h2>
        <p className="muted">Introduce los datos del suelo y del clima para recibir una recomendación.</p>
        <div className="chips">
          <span className="muted">Ejemplos:</span>
          {Object.keys(EXAMPLES).map((k) => (
            <button type="button" key={k} className="chip" onClick={() => setValues(EXAMPLES[k])}>{k}</button>
          ))}
        </div>
        <div className="fields">
          {FIELDS.map((f) => (
            <label key={f.key} className="field">
              <span>{f.label} {f.unit && <em className="muted">({f.unit})</em>}</span>
              <input
                type="number" required min={f.min} max={f.max} step={f.step}
                value={values[f.key]}
                onChange={(e) => setValues({ ...values, [f.key]: e.target.value })}
              />
            </label>
          ))}
        </div>
        <button className="btn primary" disabled={loading}>{loading ? 'Calculando…' : 'Recomendar cultivo'}</button>
        {error && <p className="alert error">{error}</p>}
      </form>

      <div className="card result">
        <h2>Resultado</h2>
        {!result && <p className="muted">Aquí aparecerá el cultivo recomendado.</p>}
        {result && (
          <>
            <div className="hero">
              <span className="hero-label">Cultivo recomendado</span>
              <span className="hero-value">{cropName(result.label)}</span>
              <span className="hero-sub">Confianza {pct(result.confidence)} · modelo v{result.model_version} · predicción #{result.id}</span>
            </div>
            <h3>Top 3 alternativas</h3>
            <BarList
              max={1}
              format={(v) => pct(v)}
              items={result.top3.map((t) => ({ label: t.label, display: cropName(t.label), value: t.probability }))}
            />
            {result.warnings.length > 0 && (
              <div className="alert warn">
                <strong>⚠ Atención:</strong> la entrada está fuera de los rangos vistos en entrenamiento, así que la
                predicción puede ser menos fiable.
                <ul>{result.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
