// Composable de autenticacion con estado singleton a nivel de modulo.
// Mismo patron que useToast: el ref vive afuera, la funcion solo expone getters/setters.

import { ref, computed, readonly } from 'vue'
import { apiRequest, getToken, setToken } from '@/lib/api'

const user = ref(null)
const loading = ref(false)
const error = ref('')

async function login(username, password) {
  loading.value = true
  error.value = ''
  try {
    const data = await apiRequest('/auth/login/', {
      method: 'POST',
      body: { username, password },
    })
    setToken(data.key)
    user.value = await apiRequest('/auth/me/')
    return true
  } catch (err) {
    error.value = err.message || 'No se pudo iniciar sesion.'
    return false
  } finally {
    loading.value = false
  }
}

async function fetchCurrentUser() {
  if (!getToken()) {
    user.value = null
    return null
  }
  try {
    user.value = await apiRequest('/auth/me/')
    return user.value
  } catch {
    user.value = null
    setToken(null)
    return null
  }
}

function logout() {
  setToken(null)
  user.value = null
  error.value = ''
}

function clearError() {
  error.value = ''
}

export function useAuth() {
  return {
    user: readonly(user),
    loading: readonly(loading),
    error: readonly(error),
    isAuthenticated: computed(() => Boolean(user.value && getToken())),
    login,
    fetchCurrentUser,
    logout,
    clearError,
  }
}
