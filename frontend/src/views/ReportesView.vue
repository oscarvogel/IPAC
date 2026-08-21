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
      :usuarios="cajeros"
      :show-user="activeTab === 'cobranzas'"
      @update:filtros="updateFiltros"
      @aplicar="aplicarFiltros"
      :export-label="'Exportar Excel'"
      @exportar="exportarActual"
    />

    <nav class="reports-tabs" aria-label="Categorías de reportes">
      <button v-for="tab in tabs" :key="tab.id" type="button" :class="{ active: activeTab === tab.id }" @click="activeTab = tab.id">
        {{ tab.label }}
      </button>
    </nav>

    <template v-if="activeTab === 'resumen'">
      <ReporteResumen :resumen="resumen" :show-distribution="false" />
    </template>

    <template v-else-if="activeTab === 'cobranzas'">
      <ReporteResumen :resumen="resumen" :show-metrics="false" />
      <section class="report-category-card">
        <header><div><p class="eyebrow">Control diario</p><h2>Cobranzas por usuario</h2></div></header>
        <div class="audit-table-wrap">
          <table class="audit-table">
            <thead><tr><th>Usuario</th><th>Pagos</th><th>Efectivo</th><th>Transferencia</th><th>Mercado Pago</th><th>Tarjeta</th><th>Otros</th><th>Total</th><th>Diferencia caja</th></tr></thead>
            <tbody>
              <tr v-for="row in cobranzasUsuarios" :key="row.usuario_id || row.usuario">
                <td><strong>{{ row.usuario }}</strong></td><td>{{ row.cantidad }}</td>
                <td>{{ money(row.efectivo) }}</td><td>{{ money(row.transferencia) }}</td><td>{{ money(row.mercado_pago) }}</td><td>{{ money(row.tarjeta) }}</td><td>{{ money(row.otro) }}</td>
                <td><strong>{{ money(row.total) }}</strong></td><td :class="{ 'report-difference': Number(row.diferencia_caja) !== 0 }">{{ money(row.diferencia_caja) }}</td>
              </tr>
              <tr v-if="!cobranzasUsuarios.length"><td colspan="9">No hay cobranzas en el período.</td></tr>
            </tbody>
          </table>
        </div>
      </section>
      <PagosListado :pagos="pagos" />
    </template>

    <section v-else-if="activeTab === 'morosidad'" class="report-category-card report-category-callout">
      <div><p class="eyebrow">Seguimiento de deuda</p><h2>Reporte de morosidad</h2><p>Consultá alumnos morosos, antigüedad, segmentos y datos de contacto.</p></div>
      <RouterLink to="/deudores">Abrir cartera de deudores</RouterLink>
    </section>

    <section v-else-if="activeTab === 'alumnos'" class="report-category-card report-category-callout">
      <div><p class="eyebrow">Administración académica</p><h2>Listado de alumnos</h2><p>Exportá el padrón visible por sucursal con datos de contacto y trayectoria actual.</p></div>
      <RouterLink to="/alumnos">Abrir directorio</RouterLink>
    </section>

    <section v-else class="report-category-card">
      <div><p class="eyebrow">Tesorería</p><h2>Cajas del período</h2><p>{{ resumen?.cajas?.cerradas || 0 }} cerradas · {{ resumen?.cajas?.abiertas || 0 }} abiertas · diferencia acumulada {{ money(resumen?.cajas?.diferencia_acumulada) }}</p></div>
      <RouterLink to="/caja">Ir a Caja</RouterLink>
    </section>
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
  cobranzasUsuarios,
  loading,
  error: reportesError,
  loadResumen,
  loadPagos,
  loadCobranzasUsuarios,
  exportarExcel,
} = useReportes()
const toast = useToast()
const pageReady = ref(false)
const pageError = ref('')
const activeTab = ref('resumen')
const cajeros = ref([])
const tabs = [
  { id: 'resumen', label: 'Resumen' },
  { id: 'cobranzas', label: 'Cobranzas' },
  { id: 'morosidad', label: 'Morosidad' },
  { id: 'caja', label: 'Caja' },
  { id: 'alumnos', label: 'Alumnos' },
]

const filtros = reactive({
  desde: '',
  hasta: '',
  sucursal: '',
  medio: '',
  usuario: '',
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
    usuario: filtros.usuario || undefined,
  }
  await Promise.all([loadResumen(payload), loadPagos(payload), loadCobranzasUsuarios(payload)])
  const known = new Map(cajeros.value.map((item) => [String(item.id), item]))
  for (const row of cobranzasUsuarios.value) {
    if (row.usuario_id) known.set(String(row.usuario_id), { id: row.usuario_id, nombre: row.usuario })
  }
  cajeros.value = [...known.values()].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
  if (reportesError.value) throw new Error(reportesError.value)
}

async function aplicarFiltros() {
  try {
    await fetchReportData()
  } catch (err) {
    toast.error(err.message || 'No se pudieron actualizar los reportes.')
  }
}

async function exportarActual() {
  const payload = {
    desde: filtros.desde || undefined,
    hasta: filtros.hasta || undefined,
    sucursal: filtros.sucursal || undefined,
    medio: filtros.medio || undefined,
    usuario: filtros.usuario || undefined,
  }
  try {
    const reportType = activeTab.value === 'morosidad'
      ? 'morosidad'
      : activeTab.value === 'caja'
        ? 'cajas'
        : activeTab.value === 'alumnos'
          ? 'alumnos'
          : 'pagos'
    await exportarExcel(reportType, payload)
    toast.success('El reporte Excel se descargó correctamente.')
  } catch (err) {
    toast.error(err.message || 'No se pudo generar el CSV.')
  }
}

function money(value) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(Number(value || 0))
}
</script>

<style scoped>
.reports-tabs { display: flex; gap: .35rem; padding: .35rem; border: 1px solid var(--border); border-radius: .85rem; background: var(--surface); overflow-x: auto; }
.reports-tabs button { min-height: 2.5rem; border: 0; border-radius: .65rem; padding: 0 1rem; background: transparent; color: var(--text-secondary); font-weight: 800; white-space: nowrap; }
.reports-tabs button.active { background: var(--primary); color: white; }
.report-category-card { padding: 1.1rem; border: 1px solid var(--border); border-radius: 1rem; background: var(--surface); }
.report-category-card h2 { margin: .2rem 0; }
.report-category-callout { display: flex; justify-content: space-between; align-items: center; gap: 1rem; }
.report-category-card > a { display: inline-flex; padding: .7rem 1rem; border-radius: .7rem; background: var(--primary); color: white; text-decoration: none; font-weight: 800; }
.report-difference { color: var(--danger); font-weight: 800; }
@media (max-width: 700px) { .report-category-callout { align-items: stretch; flex-direction: column; } }
</style>
