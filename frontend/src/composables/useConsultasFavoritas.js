import { ref, watch } from 'vue'
import { apiRequest } from '@/lib/api'
import { useAuth } from '@/composables/useAuth'

export function useConsultasFavoritas(pantalla) {
  const { user } = useAuth()
  const favoritas = ref([])
  const loading = ref(false)
  const error = ref('')
  let revision = 0
  async function load() {
    const current = ++revision
    favoritas.value = []
    error.value = ''
    if (!user.value) return
    loading.value = true
    try {
      const data = await apiRequest('/consultas-favoritas/', { query: { pantalla } })
      if (current === revision) favoritas.value = data
    } catch (err) {
      if (current === revision) error.value = err.message
    } finally {
      if (current === revision) loading.value = false
    }
  }
  watch(() => user.value?.id, () => { loading.value = false; void load() }, { immediate: true, flush: 'sync' })
  async function mutate(path, method, body) {
    const account = user.value?.id
    const data = await apiRequest(path, { method, body })
    if (account !== user.value?.id) throw new Error('La sesión cambió. Volvé a cargar tus favoritas.')
    await load()
    return data
  }
  async function obtener(id) {
    const account = user.value?.id
    const data = await apiRequest(`/consultas-favoritas/${id}/`)
    if (account !== user.value?.id) throw new Error('La sesión cambió. Volvé a cargar tus favoritas.')
    return data
  }
  return {
    favoritas, loading, error, load,
    crear: (nombre, configuracion) => mutate('/consultas-favoritas/', 'POST', { nombre, pantalla, configuracion }),
    actualizar: (id, body) => mutate(`/consultas-favoritas/${id}/`, 'PATCH', body),
    eliminar: (id) => mutate(`/consultas-favoritas/${id}/`, 'DELETE'),
    obtener,
  }
}
