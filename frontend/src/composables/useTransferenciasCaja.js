import { readonly, ref } from 'vue'
import { apiRequest } from '@/lib/api'

function nuevaClave() {
  if (globalThis.crypto.randomUUID) return globalThis.crypto.randomUUID()
  // randomUUID requiere un contexto seguro; getRandomValues también funciona
  // cuando el portal se sirve en la red local por HTTP.
  const bytes = globalThis.crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 15) | 64
  bytes[8] = (bytes[8] & 63) | 128
  const hex = [...bytes].map((value) => value.toString(16).padStart(2, '0')).join('')
  return hex.slice(0, 8) + '-' + hex.slice(8, 12) + '-' + hex.slice(12, 16)
    + '-' + hex.slice(16, 20) + '-' + hex.slice(20)
}

// Estado de esta pantalla: no abre ni consulta una caja del usuario ejecutor.
export function useTransferenciasCaja() {
  const cajasAbiertas = ref([])
  const transferencias = ref([])
  const loading = ref(false)
  const error = ref('')
  let intento = null

  async function refresh() {
    const [cajas, historial] = await Promise.all([
      apiRequest('/transferencias-caja/cajas-abiertas/'),
      apiRequest('/transferencias-caja/'),
    ])
    cajasAbiertas.value = cajas
    transferencias.value = historial
  }

  async function load() {
    loading.value = true
    error.value = ''
    try {
      await refresh()
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  async function transferir({ origen_id, destino_id, importe, motivo }) {
    if (loading.value) return null
    loading.value = true
    error.value = ''
    const body = { origen_id, destino_id, importe, motivo }
    const payload = JSON.stringify(body)
    if (!intento || intento.payload !== payload) {
      intento = { payload, key: nuevaClave() }
    }
    try {
      const saved = await apiRequest('/transferencias-caja/', {
        method: 'POST', body, headers: { 'Idempotency-Key': intento.key },
      })
      intento = null
      transferencias.value = [saved, ...transferencias.value.filter((item) => item.id !== saved.id)]
      try {
        await refresh()
      } catch (err) {
        // La escritura ya fue confirmada. Conservar evidencia evita repetirla.
        error.value = 'La transferencia se registró, pero no se pudo actualizar la lista. ' + err.message
      }
      return saved
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    cajasAbiertas: readonly(cajasAbiertas), transferencias: readonly(transferencias),
    loading: readonly(loading), error: readonly(error), load, transferir,
  }
}
