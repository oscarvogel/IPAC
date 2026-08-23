// Composable de pagos. Reusado por AlumnosView y CajaView.

import { ref, readonly } from 'vue'
import { apiRequest } from '@/lib/api'

const pagos = ref([])

async function loadPagos(query = {}) {
  const data = await apiRequest('/pagos/', { query })
  pagos.value = data.results || []
}

async function createPago(payload) {
  return await apiRequest('/pagos/', { method: 'POST', body: payload })
}

async function getRecibo(pagoId) {
  return await apiRequest(`/pagos/${pagoId}/recibo/`)
}

async function anularPago(pagoId, motivo) {
  return await apiRequest(`/pagos/${pagoId}/anular/`, {
    method: 'POST',
    body: { motivo },
  })
}

async function getEstadoCuenta(alumnoId) {
  return await apiRequest(`/alumnos/${alumnoId}/estado-cuenta/`)
}

async function generarCuota(payload) {
  return await apiRequest('/cuotas/generar/', { method: 'POST', body: payload })
}

export function usePagos() {
  return {
    pagos: readonly(pagos),
    loadPagos,
    createPago,
    getRecibo,
    anularPago,
    getEstadoCuenta,
    generarCuota,
  }
}
