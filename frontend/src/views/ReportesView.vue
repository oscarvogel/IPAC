<template>
  <section class="reports-screen">
    <ReporteFiltros
      v-model:filtros="filtros"
      :sucursales="sucursales"
      :loading="loading"
      @aplicar="aplicarFiltros"
      @exportar="exportarCsv"
    />

    <ReporteResumen :resumen="resumen" />

    <PagosListado :pagos="pagos" />
  </section>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { useCatalogos } from '@/composables/useCatalogos'
import { useReportes } from '@/composables/useReportes'
import { useToast } from '@/composables/useToast'
import ReporteFiltros from '@/components/reportes/ReporteFiltros.vue'
import ReporteResumen from '@/components/reportes/ReporteResumen.vue'
import PagosListado from '@/components/reportes/PagosListado.vue'

const { sucursales, loadCatalogos } = useCatalogos()
const { resumen, pagos, loading, loadResumen, loadPagos, exportarCsv: descargarCsv } = useReportes()
const toast = useToast()

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

onMounted(async () => {
  Object.assign(filtros, rangoPorDefecto())
  await loadCatalogos()
  await aplicarFiltros()
})

async function aplicarFiltros() {
  const payload = {
    desde: filtros.desde || undefined,
    hasta: filtros.hasta || undefined,
    sucursal: filtros.sucursal || undefined,
    medio: filtros.medio || undefined,
  }
  await Promise.all([loadResumen(payload), loadPagos(payload)])
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
  } catch (err) {
    toast.error(err.message || 'No se pudo generar el CSV.')
  }
}
</script>
