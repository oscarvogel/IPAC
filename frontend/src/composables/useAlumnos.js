// Composable para la gestion de alumnos.
// Estado singleton: lista de alumnos y el seleccionado.

import { ref, computed, readonly } from 'vue'
import { apiRequest } from '@/lib/api'

const alumnos = ref([])
const selectedAlumnoId = ref(null)
const loading = ref(false)
const error = ref('')
const pagination = ref({
  count: 0,
  page: 1,
  pageSize: 10,
  next: null,
  previous: null,
})

async function loadAlumnos(query = {}) {
  loading.value = true
  error.value = ''
  try {
    const data = await apiRequest('/alumnos/', { query })
    alumnos.value = data.results || []
    pagination.value = {
      count: Number(data.count || 0),
      page: Number(data.page || query.page || 1),
      pageSize: Number(data.page_size || 10),
      next: data.next || null,
      previous: data.previous || null,
    }
    if (!selectedAlumnoId.value && alumnos.value.length) {
      selectedAlumnoId.value = alumnos.value[0].id
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function createAlumno(payload) {
  const saved = await apiRequest('/alumnos/', { method: 'POST', body: payload })
  alumnos.value.push(saved)
  return saved
}

async function updateAlumno(id, payload) {
  const saved = await apiRequest(`/alumnos/${id}/`, { method: 'PATCH', body: payload })
  const idx = alumnos.value.findIndex((a) => a.id === id)
  if (idx >= 0) alumnos.value[idx] = saved
  return saved
}

async function setAlumnoEstado(id, estado) {
  const saved = await apiRequest(`/alumnos/${id}/`, { method: 'PATCH', body: { estado } })
  const idx = alumnos.value.findIndex((a) => a.id === id)
  if (idx >= 0) alumnos.value[idx] = saved
  return saved
}

async function deactivateAlumno(id) {
  return setAlumnoEstado(id, 'inactivo')
}

async function reactivateAlumno(id) {
  return setAlumnoEstado(id, 'activo')
}

function setSelected(id) {
  selectedAlumnoId.value = id
}

export function useAlumnos() {
  return {
    alumnos: readonly(alumnos),
    selectedAlumnoId,
    pagination: readonly(pagination),
    selectedAlumno: computed(
      () => alumnos.value.find((a) => a.id === selectedAlumnoId.value) || null,
    ),
    loading: readonly(loading),
    error: readonly(error),
    loadAlumnos,
    createAlumno,
    updateAlumno,
    deactivateAlumno,
    reactivateAlumno,
    setAlumnoEstado,
    setSelected,
  }
}
