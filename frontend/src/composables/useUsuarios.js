import { ref, readonly } from 'vue'
import { apiRequest } from '@/lib/api'

const usuarios = ref([])
const loading = ref(false)
const error = ref('')

async function loadUsuarios(query = {}) {
  loading.value = true
  error.value = ''
  try {
    const data = await apiRequest('/usuarios/', { query })
    usuarios.value = data.results || []
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function createUsuario(payload) {
  const saved = await apiRequest('/usuarios/', { method: 'POST', body: payload })
  usuarios.value.push(saved)
  return saved
}

async function updateUsuario(id, payload) {
  const saved = await apiRequest(`/usuarios/${id}/`, { method: 'PATCH', body: payload })
  const idx = usuarios.value.findIndex((u) => u.id === id)
  if (idx >= 0) usuarios.value[idx] = saved
  return saved
}

async function deactivateUsuario(id) {
  await apiRequest(`/usuarios/${id}/`, { method: 'DELETE' })
  const idx = usuarios.value.findIndex((u) => u.id === id)
  if (idx >= 0) {
    usuarios.value[idx] = { ...usuarios.value[idx], is_active: false }
  }
}

export function useUsuarios() {
  return {
    usuarios: readonly(usuarios),
    loading: readonly(loading),
    error: readonly(error),
    loadUsuarios,
    createUsuario,
    updateUsuario,
    deactivateUsuario,
  }
}
