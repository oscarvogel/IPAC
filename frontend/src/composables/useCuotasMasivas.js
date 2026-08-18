import { readonly, ref } from 'vue'
import { apiRequest } from '@/lib/api'

const PAGE_SIZE = 25

async function loadAllPages(path, query = {}) {
  const items = []
  let page = 1
  let count = 0

  do {
    const data = await apiRequest(path, {
      query: { ...query, page, page_size: PAGE_SIZE },
    })
    const results = data.results || []
    items.push(...results)
    count = Number(data.count || items.length)
    page += 1
    if (!data.next && items.length >= count) break
  } while (items.length < count)

  return items
}

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
      const [alumnos, cuotas] = await Promise.all([
        loadAllPages('/alumnos/', {
          sucursal,
          carrera: carrera || '',
          estado: 'activo',
        }),
        loadAllPages('/cuotas/'),
      ])
      const duplicados = new Set(
        cuotas
          .filter((cuota) => String(cuota.concepto) === String(concepto) && cuota.periodo === periodo)
          .map((cuota) => String(cuota.alumno)),
      )
      alumnosEncontrados.value = alumnos.length
      omitidas.value = alumnos.filter((alumno) => duplicados.has(String(alumno.id))).length
      alumnosElegibles.value = alumnos.filter((alumno) => !duplicados.has(String(alumno.id)))
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
