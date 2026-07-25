// Composable para la gestion de sucursales.
// Estado singleton: lista de sucursales.
//
// A diferencia de useCatalogos.sucursales (catalogo liviano para selects),
// este composable es el CRUD real que usa la pantalla de Sucursales: alta
// y edicion contra /api/sucursales/.

import { ref, readonly } from 'vue'
import { apiRequest } from '@/lib/api'

const sucursales = ref([])
const loading = ref(false)
const error = ref('')

async function loadSucursales(force = false) {
  // Si useCatalogos ya las cargo, las reusamos para no duplicar requests.
  if (sucursales.value.length && !force) return
  loading.value = true
  error.value = ''
  try {
    const data = await apiRequest('/sucursales/')
    sucursales.value = data.results || []
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function createSucursal(payload) {
  const saved = await apiRequest('/sucursales/', { method: 'POST', body: payload })
  sucursales.value.push(saved)
  return saved
}

async function updateSucursal(id, payload) {
  const saved = await apiRequest(`/sucursales/${id}/`, { method: 'PATCH', body: payload })
  const idx = sucursales.value.findIndex((s) => s.id === id)
  if (idx >= 0) sucursales.value[idx] = saved
  return saved
}

export function useSucursales() {
  return {
    sucursales: readonly(sucursales),
    loading: readonly(loading),
    error: readonly(error),
    loadSucursales,
    createSucursal,
    updateSucursal,
  }
}
