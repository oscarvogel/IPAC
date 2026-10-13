import { readonly, ref } from 'vue'
import { apiRequest } from '@/lib/api'

// Estado de esta pantalla: no abre ni consulta una caja del usuario ejecutor.
export function useTransferenciasCaja() {
  const cajasAbiertas = ref([])
  const transferencias = ref([])
  const loading = ref(false)
  const error = ref('')

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
    try {
      const saved = await apiRequest('/transferencias-caja/', {
        method: 'POST', body: { origen_id, destino_id, importe, motivo },
      })
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
