import { readonly, ref } from 'vue'
import { apiRequest } from '@/lib/api'

const matriculas = ref([])
const loading = ref(false)
const error = ref('')

async function loadMatriculas(alumnoId) {
  if (!alumnoId) {
    matriculas.value = []
    return []
  }
  loading.value = true
  error.value = ''
  try {
    const data = await apiRequest('/matriculas/', { query: { alumno: alumnoId } })
    matriculas.value = data.results || data || []
    return matriculas.value
  } catch (err) {
    error.value = err.message || 'No se pudieron cargar las matrículas.'
    throw err
  } finally {
    loading.value = false
  }
}

async function createMatricula(payload) {
  const saved = await apiRequest('/matriculas/', { method: 'POST', body: payload })
  matriculas.value = [saved, ...matriculas.value]
  return saved
}

async function updateMatricula(id, payload) {
  const saved = await apiRequest(`/matriculas/${id}/`, { method: 'PATCH', body: payload })
  const index = matriculas.value.findIndex((matricula) => matricula.id === id)
  if (index >= 0) matriculas.value[index] = saved
  return saved
}

async function finalizarMatricula(id, payload = {}) {
  const saved = await apiRequest(`/matriculas/${id}/finalizar/`, { method: 'POST', body: payload })
  const index = matriculas.value.findIndex((matricula) => matricula.id === id)
  if (index >= 0) matriculas.value[index] = saved
  return saved
}

async function cambiarCarrera(id, payload) {
  const saved = await apiRequest(`/matriculas/${id}/cambiar-carrera/`, { method: 'POST', body: payload })
  return saved
}

async function anularMatricula(id, motivo) {
  const saved = await apiRequest(`/matriculas/${id}/anular/`, { method: 'POST', body: { motivo } })
  return saved
}

export function useMatriculas() {
  return {
    matriculas: readonly(matriculas),
    loading: readonly(loading),
    error: readonly(error),
    loadMatriculas,
    createMatricula,
    updateMatricula,
    finalizarMatricula,
    cambiarCarrera,
    anularMatricula,
  }
}
