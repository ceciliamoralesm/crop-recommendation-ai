import { useState } from 'react'

/** Tooltip flotante compartido por los gráficos. */
function useTooltip() {
  const [tip, setTip] = useState(null)
  const show = (e, content) => {
    const r = e.currentTarget.closest('.chart').getBoundingClientRect()
    setTip({ x: e.clientX - r.left, y: e.clientY - r.top, content })
  }
  const node = tip && (
    <div className="tooltip" style={{ left: tip.x + 12, top: tip.y + 12 }} role="status">
      {tip.content}
    </div>
  )
  return { show, hide: () => setTip(null), node }
}

/**
 * Barras horizontales de una sola serie (magnitud). Sin leyenda: el título nombra la serie.
 * items: [{ label, value, display }]
 */
export function BarList({ items, max, format = (v) => v, domainMin = 0 }) {
  const t = useTooltip()
  const top = max ?? Math.max(...items.map((i) => i.value))
  return (
    <div className="chart barlist" onMouseLeave={t.hide}>
      {items.map((it) => {
        const w = Math.max(0, ((it.value - domainMin) / (top - domainMin)) * 100)
        return (
          <div
            key={it.label}
            className="bar-row"
            onMouseMove={(e) => t.show(e, <><strong>{it.display ?? it.label}</strong><br />{format(it.value)}</>)}
          >
            <span className="bar-label" title={it.display ?? it.label}>{it.display ?? it.label}</span>
            <span className="bar-track">
              <span className="bar-fill" style={{ width: `${w}%` }} />
            </span>
            <span className="bar-value">{format(it.value)}</span>
          </div>
        )
      })}
      {t.node}
    </div>
  )
}

// Rampa secuencial azul (claro -> oscuro), un solo tono.
const SEQ = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b']

/** Matriz de confusión como heatmap secuencial con tooltip por celda. */
export function ConfusionMatrix({ classes, matrix, nameOf = (c) => c }) {
  const t = useTooltip()
  const max = Math.max(...matrix.flat())
  const color = (v) => (v === 0 ? 'transparent' : SEQ[Math.min(SEQ.length - 1, Math.floor((v / max) * (SEQ.length - 1)))])
  return (
    <div className="chart cm-wrap" onMouseLeave={t.hide}>
      <table className="cm" aria-label="Matriz de confusión">
        <thead>
          <tr>
            <th className="cm-corner">Real ↓ / Predicho →</th>
            {classes.map((c) => <th key={c} className="cm-col"><span>{c}</span></th>)}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={classes[i]}>
              <th className="cm-row">{classes[i]}</th>
              {row.map((v, j) => {
                const dark = v / max > 0.45
                return (
                  <td
                    key={j}
                    className={`${i === j ? 'diag' : ''} ${v && i !== j ? 'err' : ''}`}
                    style={{ background: color(v), color: v === 0 ? undefined : dark ? '#fff' : '#0b0b0b' }}
                    onMouseMove={(e) => t.show(e, <>Real: <strong>{nameOf(classes[i])}</strong><br />Predicho: <strong>{nameOf(classes[j])}</strong><br />{v} muestras</>)}
                  >
                    {v || ''}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="cm-legend" aria-hidden="true">
        <span>0</span>
        {SEQ.map((c) => <i key={c} style={{ background: c }} />)}
        <span>{max}</span>
        <span className="muted">· las celdas fuera de la diagonal con borde son errores</span>
      </div>
      {t.node}
    </div>
  )
}
