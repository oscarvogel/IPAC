// Composable para la pantalla de reportes.
// Estado singleton: resumen operativo y listado de pagos filtrados.
//
// - `loadResumen(filtros)` consulta /api/reportes/resumen/ y devuelve
//   cobranzas, cuenta corriente y estado de cajas para el rango.
// - `loadPagos(filtros)` consulta /api/pagos/ con los mismos filtros.
// - `exportarCsv(filtros)` descarga el CSV desde /api/pagos/exportar-csv/.
//   El endpoint devuelve text/csv con BOM, lo abrimos en una nueva tab.

import { ref, readonly } from 'vue'
import { apiRequest, getToken, API_BASE_URL } from '@/lib/api'

const resumen = ref(null)
const pagos = ref([])
const loading = ref(false)
const error = ref('')
const cobranzasUsuarios = ref([])

function buildQuery(filtros) {
  const query = {}
  if (filtros?.desde) query.desde = filtros.desde
  if (filtros?.hasta) query.hasta = filtros.hasta
  if (filtros?.sucursal) query.sucursal = filtros.sucursal
  if (filtros?.medio) query.medio = filtros.medio
  return query
}

async function loadResumen(filtros = {}) {
  loading.value = true
  error.value = ''
  try {
    resumen.value = await apiRequest('/reportes/resumen/', { query: buildQuery(filtros) })
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function loadPagos(filtros = {}) {
  loading.value = true
  error.value = ''
  try {
    const data = await apiRequest('/pagos/', { query: buildQuery(filtros) })
    pagos.value = data.results || []
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function loadCobranzasUsuarios(filtros = {}) {
  const data = await apiRequest('/reportes/cobranzas-usuarios/', { query: buildQuery(filtros) })
  cobranzasUsuarios.value = data.resultados || []
}

function exportarCsv(filtros = {}) {
  const params = new URLSearchParams()
  const query = buildQuery(filtros)
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== '') {
      params.set(key, String(value))
    }
  }
  const qs = params.toString()
  const url = `${API_BASE_URL}/pagos/exportar-csv/${qs ? `?${qs}` : ''}`
  // El endpoint devuelve text/csv con attachment. Disparamos la descarga
  // agregando el header de auth via fetch + blob, y dejamos que el browser
  // ofrezca guardar el archivo.
  return fetch(url, { headers: { Authorization: `Token ${getToken()}` } })
    .then((res) => {
      if (!res.ok) throw new Error('No se pudo generar el CSV.')
      return res.blob()
    })
    .then((blob) => {
      const objectUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = objectUrl
      a.download = 'pagos-ipac.csv'
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(objectUrl)
    })
}

function exportarExcel(tipo, filtros = {}) {
  const params = new URLSearchParams({ tipo })
  for (const [key, value] of Object.entries(buildQuery(filtros))) {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value))
  }
  const url = `${API_BASE_URL}/reportes/exportar.xlsx?${params}`
  return fetch(url, { headers: { Authorization: `Token ${getToken()}` } })
    .then((res) => {
      if (!res.ok) throw new Error('No se pudo generar el archivo Excel.')
      return res.blob()
    })
    .then((blob) => {
      const objectUrl = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = objectUrl
      anchor.download = `ipac-${tipo}.xlsx`
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      URL.revokeObjectURL(objectUrl)
    })
}

function clearError() {
  error.value = ''
}

export function useReportes() {
  return {
    resumen: readonly(resumen),
    pagos: readonly(pagos),
    cobranzasUsuarios: readonly(cobranzasUsuarios),
    loading: readonly(loading),
    error: readonly(error),
    loadResumen,
    loadPagos,
    loadCobranzasUsuarios,
    exportarCsv,
    exportarExcel,
    clearError,
  }
}
