// Composable para la gestion de conceptos cobrables.
// Estado singleton: lista de conceptos cobrables.
//
// `useCatalogos` mantiene un catalogo liviano para selects en otros modulos
// (PagoForm, MatriculaForm, etc). Este composable es el que usa la pantalla
// de Conceptos para hacer CRUD: alta, edicion y desactivacion.

import { ref, readonly } from 'vue'
import { apiRequest } from '@/lib/api'

const conceptos = ref([])
const loading = ref(false)
const error = ref('')

async function loadConceptos(query = {}) {
  loading.value = true
  error.value = ''
  try {
    const data = await apiRequest('/conceptos/', { query })
    conceptos.value = data.results || []
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function createConcepto(payload) {
  const saved = await apiRequest('/conceptos/', { method: 'POST', body: payload })
  conceptos.value.push(saved)
  return saved
}

async function updateConcepto(id, payload) {
  const saved = await apiRequest(`/conceptos/${id}/`, { method: 'PATCH', body: payload })
  const idx = conceptos.value.findIndex((c) => c.id === id)
  if (idx >= 0) conceptos.value[idx] = saved
  return saved
}

async function deactivateConcepto(id) {
  await apiRequest(`/conceptos/${id}/`, { method: 'DELETE' })
  const idx = conceptos.value.findIndex((c) => c.id === id)
  if (idx >= 0) {
    conceptos.value[idx] = { ...conceptos.value[idx], activo: false }
  }
}

export function useConceptos() {
  return {
    conceptos: readonly(conceptos),
    loading: readonly(loading),
    error: readonly(error),
    loadConceptos,
    createConcepto,
    updateConcepto,
    deactivateConcepto,
  }
}
