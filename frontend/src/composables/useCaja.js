// Composable para la caja diaria.
// Estado singleton: caja del dia, totales calculados y acciones.
//
// Los totales (cajaTotales) se recalculan automaticamente cuando cambian
// los movimientos de la caja. La view no recalcula nada: solo consume.

import { ref, computed, readonly } from 'vue'
import { apiRequest } from '@/lib/api'
import { useAuth } from '@/composables/useAuth'
import { useCatalogos } from '@/composables/useCatalogos'

const cajaHoy = ref(null)
const loading = ref(false)
const error = ref('')

function resolveSucursalId(explicitId) {
  if (explicitId) return explicitId
  const { user } = useAuth()
  const fromUser = user.value?.perfil?.sucursal?.id
  if (fromUser) return fromUser
  const { sucursales } = useCatalogos()
  return sucursales.value[0]?.id || null
}

async function loadCajaHoy(sucursalId) {
  const id = resolveSucursalId(sucursalId)
  if (!id) {
    cajaHoy.value = null
    return
  }
  loading.value = true
  error.value = ''
  try {
    cajaHoy.value = await apiRequest('/cajas/hoy/', { query: { sucursal: id } })
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function createMovimiento(payload) {
  if (!cajaHoy.value) return null
  loading.value = true
  error.value = ''
  try {
    const saved = await apiRequest('/movimientos-caja/', { method: 'POST', body: payload })
    await loadCajaHoy()
    return saved
  } catch (err) {
    error.value = err.message
    throw err
  } finally {
    loading.value = false
  }
}

async function cerrarCaja(totalContado) {
  if (!cajaHoy.value) return null
  loading.value = true
  error.value = ''
  try {
    cajaHoy.value = await apiRequest(`/cajas/${cajaHoy.value.id}/cerrar/`, {
      method: 'POST',
      body: { total_contado: totalContado },
    })
    return cajaHoy.value
  } catch (err) {
    error.value = err.message
    throw err
  } finally {
    loading.value = false
  }
}

function clearError() {
  error.value = ''
}

const cajaMovimientos = computed(() => cajaHoy.value?.movimientos || [])

// Logica pura de totales. Vive afuera del computed para poder testearla
// sin tener que instanciar el composable ni mockear la API.
const TIPOS_NEGATIVOS = new Set(['egreso', 'retiro', 'pase'])
const MEDIOS_INICIALES = { total: 0, efectivo: 0, transferencia: 0, tarjeta: 0, otro: 0 }

export function calcularTotalesCaja(movimientos = []) {
  return movimientos.reduce((acc, movimiento) => {
    const amount = Number(movimiento.importe || 0)
    const signed = TIPOS_NEGATIVOS.has(movimiento.tipo) ? -amount : amount
    acc.total += signed
    acc[movimiento.medio] = (acc[movimiento.medio] || 0) + signed
    return acc
  }, { ...MEDIOS_INICIALES })
}

const cajaTotales = computed(() => calcularTotalesCaja(cajaMovimientos.value))

export function useCaja() {
  return {
    cajaHoy: readonly(cajaHoy),
    cajaMovimientos,
    cajaTotales,
    loading: readonly(loading),
    error: readonly(error),
    loadCajaHoy,
    createMovimiento,
    cerrarCaja,
    clearError,
  }
}
