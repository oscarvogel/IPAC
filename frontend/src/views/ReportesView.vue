<template>
  <section class="reports-workspace text-text-primary">
    <AppPageState
      v-if="!pageReady"
      :loading="!pageError"
      :error="pageError"
      label="los reportes"
      @retry="loadPage"
    />
    <template v-else>
    <ReporteFiltros
      :filtros="filtros"
      :sucursales="sucursales"
      :loading="loading"
      @update:filtros="updateFiltros"
      @aplicar="aplicarFiltros"
      @exportar="exportarCsv"
    />

    <ReporteResumen :resumen="resumen" />

    <PagosListado :pagos="pagos" />
    </template>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useCatalogos } from '@/composables/useCatalogos'
import { useReportes } from '@/composables/useReportes'
import { useToast } from '@/composables/useToast'
import ReporteFiltros from '@/components/reportes/ReporteFiltros.vue'
import ReporteResumen from '@/components/reportes/ReporteResumen.vue'
import PagosListado from '@/components/reportes/PagosListado.vue'
import AppPageState from '@/components/ui/AppPageState.vue'

const { sucursales, loadCatalogos } = useCatalogos()
const {
  resumen,
  pagos,
  loading,
  error: reportesError,
  loadResumen,
  loadPagos,
  exportarCsv: descargarCsv,
} = useReportes()
const toast = useToast()
const pageReady = ref(false)
const pageError = ref('')

const filtros = reactive({
  desde: '',
  hasta: '',
  sucursal: '',
  medio: '',
})

function rangoPorDefecto() {
  const hoy = new Date()
  const primero = new Date(hoy.getFullYear(), hoy.getMonth(), 1)
  const iso = (d) => d.toISOString().slice(0, 10)
  return { desde: iso(primero), hasta: iso(hoy) }
}

function updateFiltros(nextFilters) {
  Object.assign(filtros, nextFilters)
}

onMounted(loadPage)

async function loadPage() {
  pageReady.value = false
  pageError.value = ''
  Object.assign(filtros, rangoPorDefecto())
  try {
    await loadCatalogos()
    await fetchReportData()
    pageReady.value = true
  } catch (err) {
    pageError.value = err.message || 'No se pudieron cargar los reportes.'
  }
}

async function fetchReportData() {
  const payload = {
    desde: filtros.desde || undefined,
    hasta: filtros.hasta || undefined,
    sucursal: filtros.sucursal || undefined,
    medio: filtros.medio || undefined,
  }
  await Promise.all([loadResumen(payload), loadPagos(payload)])
  if (reportesError.value) throw new Error(reportesError.value)
}

async function aplicarFiltros() {
  try {
    await fetchReportData()
  } catch (err) {
    toast.error(err.message || 'No se pudieron actualizar los reportes.')
  }
}

async function exportarCsv() {
  const payload = {
    desde: filtros.desde || undefined,
    hasta: filtros.hasta || undefined,
    sucursal: filtros.sucursal || undefined,
    medio: filtros.medio || undefined,
  }
  try {
    await descargarCsv(payload)
    toast.success('El reporte CSV se descargó correctamente.')
  } catch (err) {
    toast.error(err.message || 'No se pudo generar el CSV.')
  }
}
</script>
