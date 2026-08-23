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
const saldoAnterior = ref(null)
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
    const saldo = await apiRequest(`/cajas/${cajaHoy.value.id}/saldo-anterior/`)
    saldoAnterior.value = saldo?.disponible ? saldo : null
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

async function cerrarCaja(cierre) {
  if (!cajaHoy.value) return null
  loading.value = true
  error.value = ''
  try {
    cajaHoy.value = await apiRequest(`/cajas/${cajaHoy.value.id}/cerrar/`, {
      method: 'POST',
      body: typeof cierre === 'object' ? cierre : { total_contado: cierre },
    })
    saldoAnterior.value = null
    return cajaHoy.value
  } catch (err) {
    error.value = err.message
    throw err
  } finally {
    loading.value = false
  }
}

async function aplicarSaldoAnterior() {
  if (!cajaHoy.value || !saldoAnterior.value) return null
  loading.value = true
  error.value = ''
  try {
    cajaHoy.value = await apiRequest(`/cajas/${cajaHoy.value.id}/saldo-anterior/`, {
      method: 'POST',
      body: { saldo_id: saldoAnterior.value.id },
    })
    saldoAnterior.value = null
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

function amount(value) {
  return Number(value || 0)
}

export function mapearResumenCaja(caja = null) {
  const resumen = caja?.resumen || {}
  const efectivoEsperado = amount(resumen.efectivo_esperado ?? caja?.total_esperado)
  return {
    saldoInicial: amount(resumen.saldo_inicial ?? caja?.saldo_inicial),
    cobranzasEfectivo: amount(resumen.cobranzas_efectivo),
    otrosIngresosEfectivo: amount(resumen.otros_ingresos_efectivo),
    egresosEfectivo: amount(resumen.egresos_efectivo),
    retirosEfectivo: amount(resumen.retiros_efectivo),
    efectivoEsperado,
    saldoFinalFisico: amount(caja?.saldo_final_fisico ?? efectivoEsperado),
    totalIngresos: amount(resumen.total_ingresos),
    totalEgresos: amount(resumen.total_egresos),
    totalCobrado: amount(resumen.total_cobrado),
    efectivo: amount(resumen.efectivo),
    transferencia: amount(resumen.transferencia),
    mercadoPago: amount(resumen.mercado_pago),
    tarjeta: amount(resumen.tarjeta),
    otro: amount(resumen.otro),
    total: efectivoEsperado,
  }
}

const cajaTotales = computed(() => mapearResumenCaja(cajaHoy.value))

export function useCaja() {
  return {
    cajaHoy: readonly(cajaHoy),
    saldoAnterior: readonly(saldoAnterior),
    cajaMovimientos,
    cajaTotales,
    loading: readonly(loading),
    error: readonly(error),
    loadCajaHoy,
    createMovimiento,
    aplicarSaldoAnterior,
    cerrarCaja,
    clearError,
  }
}
