// Composable para la gestion de carreras y cursos.
// Estado singleton: lista de carreras y cursos.
//
// `useCatalogos` mantiene un catalogo liviano para selects en otros modulos
// (Alumnos, Conceptos, Deudores). Este composable es el que usa la pantalla de
// Carreras para hacer CRUD: alta, edicion y desactivacion.
//
// La baja es una desactivacion (activa=false) y no un DELETE: la carrera tiene
// PROTECT contra Alumno, Matricula y ConceptoCobrable, asi que borrarla
// romperia el historial de anyone que la haya cursado.

import { ref, readonly } from 'vue'
import { apiRequest } from '@/lib/api'

const carreras = ref([])
const loading = ref(false)
const error = ref('')

async function loadCarreras(query = {}) {
  loading.value = true
  error.value = ''
  try {
    const data = await apiRequest('/carreras/', { query })
    carreras.value = data.results || []
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function createCarrera(payload) {
  const saved = await apiRequest('/carreras/', { method: 'POST', body: payload })
  carreras.value.push(saved)
  return saved
}

async function updateCarrera(id, payload) {
  const saved = await apiRequest(`/carreras/${id}/`, { method: 'PATCH', body: payload })
  const idx = carreras.value.findIndex((c) => c.id === id)
  if (idx >= 0) carreras.value[idx] = saved
  return saved
}

async function deactivateCarrera(id) {
  const saved = await apiRequest(`/carreras/${id}/`, { method: 'PATCH', body: { activa: false } })
  const idx = carreras.value.findIndex((c) => c.id === id)
  if (idx >= 0) carreras.value[idx] = saved
  return saved
}

export function useCarreras() {
  return {
    carreras: readonly(carreras),
    loading: readonly(loading),
    error: readonly(error),
    loadCarreras,
    createCarrera,
    updateCarrera,
    deactivateCarrera,
  }
}