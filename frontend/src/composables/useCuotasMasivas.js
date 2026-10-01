import { readonly, ref } from 'vue'
import { apiRequest } from '@/lib/api'

/**
 * Generacion de cuotas masivas.
 *
 * `plan` describe que se va a generar y es uno de dos caminos:
 *   - lote:  { cantidad, mes_inicial, anio_inicial, dia_vencimiento }
 *   - mes:   { periodo, fecha_vencimiento }
 *
 * El backend decide cual de los dos es segun si viene `cantidad`. Este modulo
 * no reimplementa esa regla: solo reenvia el plan y guarda lo que vuelve.
 */
export function useCuotasMasivas() {
  const alumnosElegibles = ref([])
  const alumnosEncontrados = ref(0)
  const omitidas = ref(0)
  const detalleAlumnos = ref([])
  const periodos = ref([])
  const etiquetasPeriodo = ref([])
  const cuotasAGenerar = ref(0)
  const loading = ref(false)
  const error = ref('')

  function limpiar() {
    alumnosElegibles.value = []
    alumnosEncontrados.value = 0
    omitidas.value = 0
    detalleAlumnos.value = []
    periodos.value = []
    etiquetasPeriodo.value = []
    cuotasAGenerar.value = 0
    error.value = ''
  }

  async function evaluar({ sucursal, carrera, concepto, plan }) {
    limpiar()
    if (!sucursal || !concepto || !plan) return

    loading.value = true
    try {
      const data = await apiRequest('/cuotas/evaluar-generacion/', {
        method: 'POST',
        body: { sucursal, carrera: carrera || null, concepto, ...plan },
      })
      alumnosEncontrados.value = Number(data.alumnos_encontrados || 0)
      omitidas.value = Number(data.omitidas || 0)
      periodos.value = Array.isArray(data.periodos) ? data.periodos : []
      etiquetasPeriodo.value = Array.isArray(data.etiquetas_periodo) ? data.etiquetas_periodo : []
      cuotasAGenerar.value = Number(data.cuotas_a_generar || 0)
      detalleAlumnos.value = Array.isArray(data.detalle_alumnos) ? data.detalle_alumnos : []
      const detailById = new Map(detalleAlumnos.value.map((alumno) => [String(alumno.id), alumno]))
      alumnosElegibles.value = (data.alumnos_elegibles || []).map((id) => detailById.get(String(id)) || { id })
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
    detalleAlumnos: readonly(detalleAlumnos),
    periodos: readonly(periodos),
    etiquetasPeriodo: readonly(etiquetasPeriodo),
    cuotasAGenerar: readonly(cuotasAGenerar),
    loading: readonly(loading),
    error: readonly(error),
    evaluar,
    generar,
  }
}
