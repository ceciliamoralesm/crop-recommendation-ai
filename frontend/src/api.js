export const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8001/api'

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, options)
  const body = res.headers.get('content-type')?.includes('application/json') ? await res.json() : await res.text()
  if (!res.ok) {
    const detail = body?.detail
    const msg = Array.isArray(detail)
      ? detail.map((d) => `${d.loc?.at(-1)}: ${d.msg}`).join(' · ')
      : detail ?? `Error ${res.status}`
    throw new Error(msg)
  }
  return body
}

const json = (method, data) => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
})

export const api = {
  health: () => request('/health'),
  predict: (data) => request('/predict', json('POST', data)),
  predictions: ({ page = 1, size = 10, label } = {}) =>
    request(`/predictions?page=${page}&size=${size}${label ? `&label=${encodeURIComponent(label)}` : ''}`),
  metrics: (version) => request(`/metrics${version ? `?version=${version}` : ''}`),
  models: () => request('/models'),
  activate: (version) => request(`/models/${version}/activate`, { method: 'POST' }),
  retrain: (force = false) => request(`/retrain?force=${force}`, { method: 'POST' }),
  datasets: () => request('/datasets'),
  toggleDataset: (id, isActive) => request(`/datasets/${id}?is_active=${isActive}`, { method: 'PATCH' }),
  upload: (file, mode, retrain) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('mode', mode)
    fd.append('retrain', String(retrain))
    return request('/datasets/upload', { method: 'POST', body: fd })
  },
  templateUrl: `${API_URL}/datasets/template`,
}

export const CROP_ES = {
  rice: 'Arroz', maize: 'Maíz', chickpea: 'Garbanzo', kidneybeans: 'Frijol rojo', pigeonpeas: 'Guandú',
  mothbeans: 'Frijol polilla', mungbean: 'Frijol mungo', blackgram: 'Frijol negro', lentil: 'Lenteja',
  pomegranate: 'Granada', banana: 'Banano', mango: 'Mango', grapes: 'Uva', watermelon: 'Sandía',
  muskmelon: 'Melón', apple: 'Manzana', orange: 'Naranja', papaya: 'Papaya', coconut: 'Coco',
  cotton: 'Algodón', jute: 'Yute', coffee: 'Café',
}
export const cropName = (l) => (CROP_ES[l] ? `${CROP_ES[l]} (${l})` : l)

export const FIELDS = [
  { key: 'N', label: 'Nitrógeno (N)', unit: 'kg/ha', min: 0, max: 300, step: 1 },
  { key: 'P', label: 'Fósforo (P)', unit: 'kg/ha', min: 0, max: 300, step: 1 },
  { key: 'K', label: 'Potasio (K)', unit: 'kg/ha', min: 0, max: 300, step: 1 },
  { key: 'temperature', label: 'Temperatura', unit: '°C', min: -10, max: 60, step: 0.1 },
  { key: 'humidity', label: 'Humedad', unit: '%', min: 0, max: 100, step: 0.1 },
  { key: 'ph', label: 'pH del suelo', unit: '', min: 0, max: 14, step: 0.01 },
  { key: 'rainfall', label: 'Precipitación', unit: 'mm', min: 0, max: 1000, step: 0.1 },
]

export const pct = (v, d = 1) => `${(v * 100).toFixed(d)} %`
export const fmtDate = (s) => new Date(s).toLocaleString('es')
