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
      :loading="loading || activeSectionLoading"
      :usuarios="cajeros"
      :show-user="activeTab === 'cobranzas'"
      @update:filtros="updateFiltros"
      @aplicar="aplicarFiltros"
      :export-label="'Exportar Excel'"
      @exportar="exportarActual"
    />

    <nav class="reports-tabs" aria-label="Categorías de reportes">
      <button v-for="tab in tabs" :key="tab.id" type="button" :class="{ active: activeTab === tab.id }" @click="selectTab(tab.id)">
        {{ tab.label }}
      </button>
    </nav>

    <AppPageState
      v-if="activeSectionLoading || activeSectionError"
      :loading="activeSectionLoading"
      :error="activeSectionError"
      label="el reporte seleccionado"
      @retry="retryActiveSection"
    />

    <Transition v-else :css="false" @enter="enterSection" @leave="leaveSection">
      <div :key="activeTab" class="reports-section-motion">
    <template v-if="activeTab === 'resumen'">
      <ReporteResumen :resumen="resumen" :show-distribution="false" />
    </template>

    <template v-else-if="activeTab === 'cobranzas'">
      <ReporteResumen :resumen="resumen" :show-metrics="false" />
      <section v-reveal-on-scroll class="report-category-card">
        <header><div><p class="eyebrow">Control diario</p><h2>Cobranzas por usuario</h2></div></header>
        <div class="reports-cobranzas-table-wrap">
          <table class="audit-table">
            <thead><tr><th>Usuario</th><th>Pagos</th><th>Efectivo</th><th>Transferencia</th><th>Mercado Pago</th><th>Tarjeta</th><th>Otros</th><th>Total</th><th>Diferencia caja</th></tr></thead>
            <MotionList tag="tbody" data-motion-list="cobranzas-usuarios-desktop">
              <tr v-for="row in cobranzasUsuarios" :key="row.usuario_id || row.usuario" data-motion-item>
                <td><strong>{{ row.usuario }}</strong></td><td>{{ row.cantidad }}</td>
                <td>{{ money(row.efectivo) }}</td><td>{{ money(row.transferencia) }}</td><td>{{ money(row.mercado_pago) }}</td><td>{{ money(row.tarjeta) }}</td><td>{{ money(row.otro) }}</td>
                <td><strong>{{ money(row.total) }}</strong></td><td :class="{ 'report-difference': Number(row.diferencia_caja) !== 0 }">{{ money(row.diferencia_caja) }}</td>
              </tr>
              <tr v-if="!cobranzasUsuarios.length" key="cobranzas-empty"><td colspan="9">No hay cobranzas en el período.</td></tr>
            </MotionList>
          </table>
        </div>
        <MotionList v-if="cobranzasUsuarios.length" class="mobile-record-list reports-cobranzas-mobile-list" data-motion-list="cobranzas-usuarios-mobile" role="list">
          <article v-for="row in cobranzasUsuarios" :key="`mobile-${row.usuario_id || row.usuario}`" data-motion-item class="mobile-record-card" role="listitem">
            <header class="mobile-record-head">
              <span class="mobile-record-icon info" aria-hidden="true"><BanknotesIcon /></span>
              <span class="mobile-record-title">
                <strong>{{ row.usuario }}</strong>
                <small>{{ row.cantidad }} {{ row.cantidad === 1 ? 'pago' : 'pagos' }}</small>
              </span>
              <strong class="mobile-record-amount">{{ money(row.total) }}</strong>
            </header>
            <dl class="mobile-record-meta">
              <div><dt>Efectivo</dt><dd>{{ money(row.efectivo) }}</dd></div>
              <div><dt>Transferencia</dt><dd>{{ money(row.transferencia) }}</dd></div>
              <div><dt>Mercado Pago</dt><dd>{{ money(row.mercado_pago) }}</dd></div>
              <div><dt>Tarjeta</dt><dd>{{ money(row.tarjeta) }}</dd></div>
              <div><dt>Otros</dt><dd>{{ money(row.otro) }}</dd></div>
              <div><dt>Diferencia caja</dt><dd :class="{ 'report-difference': Number(row.diferencia_caja) !== 0 }">{{ money(row.diferencia_caja) }}</dd></div>
            </dl>
          </article>
        </MotionList>
        <p v-if="!cobranzasUsuarios.length" class="reports-cobranzas-mobile-empty">No hay cobranzas en el período.</p>
      </section>
      <PagosListado :pagos="pagos" />
    </template>

    <section v-else-if="activeTab === 'morosidad'" v-reveal-on-scroll class="report-category-card report-category-callout">
      <div><p class="eyebrow">Seguimiento de deuda</p><h2>Reporte de morosidad</h2><p>Consultá alumnos morosos, antigüedad, segmentos y datos de contacto.</p></div>
      <RouterLink to="/deudores">Abrir cartera de deudores</RouterLink>
    </section>

    <section v-else-if="activeTab === 'alumnos'" v-reveal-on-scroll class="report-category-card report-category-callout">
      <div><p class="eyebrow">Administración académica</p><h2>Listado de alumnos</h2><p>Exportá el padrón visible por sucursal con datos de contacto y trayectoria actual.</p></div>
      <RouterLink to="/alumnos">Abrir directorio</RouterLink>
    </section>

    <section v-else v-reveal-on-scroll class="report-category-card">
      <div><p class="eyebrow">Tesorería</p><h2>Cajas del período</h2><p>{{ resumen?.cajas?.cerradas || 0 }} cerradas · {{ resumen?.cajas?.abiertas || 0 }} abiertas · diferencia acumulada {{ money(resumen?.cajas?.diferencia_acumulada) }}</p></div>
      <RouterLink to="/caja">Ir a Caja</RouterLink>
    </section>
      </div>
    </Transition>
    </template>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BanknotesIcon } from '@heroicons/vue/24/outline'
import { useCatalogos } from '@/composables/useCatalogos'
import { useReportes } from '@/composables/useReportes'
import { useToast } from '@/composables/useToast'
import ReporteFiltros from '@/components/reportes/ReporteFiltros.vue'
import ReporteResumen from '@/components/reportes/ReporteResumen.vue'
import PagosListado from '@/components/reportes/PagosListado.vue'
import AppPageState from '@/components/ui/AppPageState.vue'
import MotionList from '@/components/ui/MotionList.vue'
import { animateSectionEnter, animateSectionLeave } from '@/lib/motion'
import { vRevealOnScroll } from '@/directives/motion'

const { sucursales, loadCatalogo, loadCatalogos } = useCatalogos()
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
const route = useRoute()
const router = useRouter()
const pageReady = ref(false)
const pageError = ref('')
const activeSectionLoading = ref(false)
const activeSectionError = ref('')
const loadedResources = new Set()
let sectionRequestId = 0
const reportSections = ['resumen', 'cobranzas', 'morosidad', 'caja', 'alumnos']
const activeTab = ref(reportSections.includes(route.query.seccion) ? route.query.seccion : 'resumen')
const cajeros = ref([])
const tabs = [
  { id: 'resumen', label: 'Resumen' },
  { id: 'cobranzas', label: 'Cobranzas' },
  { id: 'morosidad', label: 'Morosidad' },
  { id: 'caja', label: 'Caja' },
  { id: 'alumnos', label: 'Alumnos' },
]

watch(
  () => route.query.seccion,
  (section) => {
    if (reportSections.includes(section)) {
      activeTab.value = section
      return
    }
    activeTab.value = 'resumen'
    if (section) router.replace({ path: route.path, query: { ...route.query, seccion: 'resumen' }, hash: route.hash })
  },
)

watch(activeTab, (section, previousSection) => {
  if (!pageReady.value || section === previousSection) return
  void fetchReportData().catch(() => {})
})

function selectTab(section) {
  if (!reportSections.includes(section)) return
  activeTab.value = section
  if (route.query.seccion === section) return
  router.push({ path: route.path, query: { ...route.query, seccion: section }, hash: route.hash })
}

function enterSection(element, done) {
  animateSectionEnter(element, done)
}

function leaveSection(element, done) {
  animateSectionLeave(element, done)
}

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
    await (loadCatalogo?.('sucursales') || loadCatalogos())
    loadedResources.clear()
    await fetchReportData({ force: true })
    pageReady.value = true
  } catch (err) {
    pageError.value = err.message || 'No se pudieron cargar los reportes.'
  }
}

async function fetchReportData({ force = false } = {}) {
  const section = activeTab.value
  const payload = {
    desde: filtros.desde || undefined,
    hasta: filtros.hasta || undefined,
    sucursal: filtros.sucursal || undefined,
    medio: filtros.medio || undefined,
    usuario: filtros.usuario || undefined,
  }
  const resourceLoaders = {
    resumen: () => loadResumen(payload),
    pagos: () => loadPagos(payload),
    cobranzasUsuarios: () => loadCobranzasUsuarios(payload),
  }
  const requiredResources = section === 'cobranzas'
    ? ['resumen', 'pagos', 'cobranzasUsuarios']
    : section === 'resumen'
      ? ['resumen']
      : section === 'caja'
        ? ['resumen']
        : []
  const pendingResources = requiredResources.filter((resource) => force || !loadedResources.has(resource))
  const requestId = ++sectionRequestId
  activeSectionLoading.value = true
  activeSectionError.value = ''
  try {
    await Promise.all(pendingResources.map(async (resource) => {
      await resourceLoaders[resource]()
      loadedResources.add(resource)
    }))
    if (pendingResources.length && reportesError.value) throw new Error(reportesError.value)
    if (section === 'cobranzas') {
      const known = new Map(cajeros.value.map((item) => [String(item.id), item]))
      for (const row of cobranzasUsuarios.value) {
        if (row.usuario_id) known.set(String(row.usuario_id), { id: row.usuario_id, nombre: row.usuario })
      }
      cajeros.value = [...known.values()].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
    }
  } catch (err) {
    if (requestId === sectionRequestId) activeSectionError.value = err.message || 'No se pudo cargar el reporte seleccionado.'
    throw err
  } finally {
    if (requestId === sectionRequestId) activeSectionLoading.value = false
  }
}

function retryActiveSection() {
  return fetchReportData({ force: true }).catch(() => {})
}

async function aplicarFiltros() {
  try {
    loadedResources.clear()
    await fetchReportData({ force: true })
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
.reports-tabs button.active { background: var(--primary); color: var(--on-primary); }
.reports-cobranzas-table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 1rem; background: var(--surface); }
.reports-cobranzas-table-wrap .audit-table { width: 100%; min-width: 850px; border-collapse: collapse; }
.reports-cobranzas-table-wrap th, .reports-cobranzas-table-wrap td { padding: .8rem 1rem; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }
.reports-cobranzas-table-wrap th { color: var(--text-secondary); font-size: .72rem; text-transform: uppercase; letter-spacing: .04em; }
.reports-cobranzas-mobile-list, .reports-cobranzas-mobile-empty { display: none; }
.report-category-card { padding: 1.1rem; border: 1px solid var(--border); border-radius: 1rem; background: var(--surface); }
.report-category-card h2 { margin: .2rem 0; }
.report-category-callout { display: flex; justify-content: space-between; align-items: center; gap: 1rem; }
.report-category-card > a { display: inline-flex; padding: .7rem 1rem; border-radius: .7rem; background: var(--primary); color: var(--on-primary); text-decoration: none; font-weight: 800; }
.report-difference { color: var(--danger); font-weight: 800; }
@media (max-width: 700px) { .report-category-callout { align-items: stretch; flex-direction: column; } }
@media (max-width: 760px) {
  .reports-tabs { overflow: visible; flex-wrap: wrap; }
  .reports-tabs button { flex: 1 1 calc(50% - .35rem); min-width: 0; }
  .reports-cobranzas-table-wrap { display: none; }
  .reports-cobranzas-mobile-list { display: grid; }
  .reports-cobranzas-mobile-empty { display: block; margin: 0; padding: 1.25rem; border: 1px solid var(--border); border-radius: 1rem; color: var(--text-secondary); background: var(--surface); text-align: center; }
}
</style>
