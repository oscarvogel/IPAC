import { readonly, ref } from 'vue'
import { apiRequest } from '@/lib/api'

export function useCuotasMasivas() {
  const alumnosElegibles = ref([])
  const alumnosEncontrados = ref(0)
  const omitidas = ref(0)
  const loading = ref(false)
  const error = ref('')

  async function evaluar({ sucursal, carrera, concepto, periodo }) {
    alumnosElegibles.value = []
    alumnosEncontrados.value = 0
    omitidas.value = 0
    error.value = ''
    if (!sucursal || !concepto || !periodo) return

    loading.value = true
    try {
      const data = await apiRequest('/cuotas/evaluar-generacion/', {
        method: 'POST',
        body: { sucursal, carrera: carrera || null, concepto, periodo },
      })
      alumnosEncontrados.value = Number(data.alumnos_encontrados || 0)
      omitidas.value = Number(data.omitidas || 0)
      alumnosElegibles.value = (data.alumnos_elegibles || []).map((id) => ({ id }))
    } catch (err) {
      error.value = err.message || 'No se pudo calcular el grupo de alumnos.'
    } finally {
      loading.value = false
    }
  }

  async function generar(payload) {
    return apiRequest('/cuotas/generar/', { method: 'POST', body: payload })
  }

  return {
    alumnosElegibles: readonly(alumnosElegibles),
    alumnosEncontrados: readonly(alumnosEncontrados),
    omitidas: readonly(omitidas),
    loading: readonly(loading),
    error: readonly(error),
    evaluar,
    generar,
  }
}
