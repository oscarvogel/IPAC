// Composable de autenticacion con estado singleton a nivel de modulo.
// Mismo patron que useToast: el ref vive afuera, la funcion solo expone getters/setters.

import { ref, computed, readonly } from 'vue'
import { apiRequest, getToken, setToken } from '@/lib/api'
import { can as canPermission, roleOf } from '@/lib/permissions'

const user = ref(null)
const loading = ref(false)
const error = ref('')

const mustChangePassword = computed(() => Boolean(user.value?.perfil?.debe_cambiar_clave))

async function login(username, password, { remember = true } = {}) {
  loading.value = true
  error.value = ''
  try {
    const data = await apiRequest('/auth/login/', {
      method: 'POST',
      body: { username, password },
    })
    setToken(data.key, { persistent: remember })
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

async function changePassword(newPassword, confirmation) {
  loading.value = true
  error.value = ''
  try {
    await apiRequest('/auth/change-password/', {
      method: 'POST',
      body: {
        new_password: newPassword,
        new_password_confirmation: confirmation,
      },
    })
    await fetchCurrentUser()
    return true
  } catch (err) {
    error.value = err.message || 'No se pudo cambiar la clave.'
    return false
  } finally {
    loading.value = false
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
    role: computed(() => roleOf(user.value)),
    can: (capability) => canPermission(user.value, capability),
    loading: readonly(loading),
    error: readonly(error),
    isAuthenticated: computed(() => Boolean(user.value && getToken())),
    mustChangePassword,
    login,
    changePassword,
    fetchCurrentUser,
    logout,
    clearError,
  }
}
