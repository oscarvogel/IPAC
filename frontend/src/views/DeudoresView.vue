<template>
  <section class="debtors-screen students-screen text-text-primary">
    <AppPageState
      v-if="!pageReady"
      :loading="!pageError"
      :error="pageError"
      label="la cartera de deudores"
      @retry="loadPage"
    />

    <template v-else>
      <section class="students-toolbar debtors-toolbar border-border bg-surface" aria-label="Filtros de deudores">
        <div class="students-toolbar-heading">
          <span class="students-toolbar-icon">
            <BanknotesIcon aria-hidden="true" />
          </span>
          <div>
            <p class="eyebrow">Cobranzas</p>
            <h2>Deudores</h2>
            <p>Priorizá la gestión por importe y antigüedad de deuda.</p>
          </div>
        </div>

        <div class="debtors-filters">
          <label class="students-search-field debtors-search-field">
            <MagnifyingGlassIcon aria-hidden="true" />
            <span class="sr-only">Buscar deudor</span>
            <input v-model="search" type="search" placeholder="Alumno, DNI o legajo" />
          </label>

          <label class="students-branch-field">
            <BuildingStorefrontIcon aria-hidden="true" />
            <span class="sr-only">Filtrar por sucursal</span>
            <select v-model="sucursalFilter">
              <option value="todas">Todas las sucursales</option>
              <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
                {{ sucursal.nombre }}
              </option>
            </select>
            <ChevronDownIcon class="students-select-chevron" aria-hidden="true" />
          </label>

          <label class="debtors-filter-field">
            <span class="sr-only">Filtrar por carrera</span>
            <select v-model="carreraFilter" aria-label="Filtrar por carrera">
              <option value="">Todas las carreras</option>
              <option v-for="carrera in careerOptions" :key="carrera.id" :value="carrera.id">
                {{ carrera.nombre }}
              </option>
            </select>
          </label>

          <label class="students-active-filter" :class="{ active: onlyOverdue }">
            <input v-model="onlyOverdue" class="sr-only" type="checkbox" />
            <ExclamationCircleIcon aria-hidden="true" />
            <span>Vencidas</span>
          </label>

          <label class="debtors-amount-field">
            <span class="sr-only">Deuda mínima</span>
            <input v-model="deudaMin" type="number" min="0" step="0.01" placeholder="Deuda desde" aria-label="Deuda desde" />
          </label>
          <label class="debtors-amount-field">
            <span class="sr-only">Deuda máxima</span>
            <input v-model="deudaMax" type="number" min="0" step="0.01" placeholder="Deuda hasta" aria-label="Deuda hasta" />
          </label>

          <label class="debtors-order-field">
            <span class="sr-only">Ordenar deudores</span>
            <select v-model="ordering" aria-label="Ordenar deudores">
              <option value="deuda">Mayor deuda</option>
              <option value="antiguedad">Mayor antigüedad</option>
            </select>
          </label>

          <label class="debtors-filter-field">
            <span class="sr-only">Mes correspondiente</span>
            <input v-model.trim="periodo" placeholder="Mes (MM-AAAA)" aria-label="Mes correspondiente" />
          </label>

          <label class="debtors-order-field">
            <span class="sr-only">Segmento de morosidad</span>
            <select v-model="segmento" aria-label="Segmento de morosidad">
              <option value="">Todas las antigüedades</option>
              <option value="1">1 cuota vencida</option>
              <option value="2">2 cuotas vencidas</option>
              <option value="3plus">3 o más cuotas vencidas</option>
            </select>
          </label>

          <button type="button" class="debtors-export" @click="exportDebt"><ArrowDownTrayIcon aria-hidden="true" /> Exportar Excel</button>
        </div>
      </section>

      <section class="debtors-summary border-border bg-surface" aria-live="polite">
        <strong>{{ pagination.count }}</strong>
        <span>{{ pagination.count === 1 ? 'alumno con saldo pendiente' : 'alumnos con saldo pendiente' }}</span>
      </section>

      <section class="debtors-table-wrap border-border bg-surface">
        <div v-if="loading" class="debtors-loading" aria-live="polite">Cargando cartera...</div>
        <div v-else-if="!deudores.length" class="students-empty-state debtors-empty">
          <span><BanknotesIcon aria-hidden="true" /></span>
          <strong>No encontramos deudores</strong>
          <p>Probá cambiando la búsqueda o los filtros seleccionados.</p>
        </div>
        <div v-else class="users-table-wrap">
          <table class="users-table debtors-table">
            <thead>
              <tr>
                <th>Alumno</th>
                <th>Ubicación académica</th>
                <th>Deuda</th>
                <th>Cuotas</th>
                <th>Antigüedad</th>
                <th>Último pago</th>
                <th><span class="sr-only">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="deudor in deudores" :key="deudor.id">
                <td>
                  <strong>{{ deudor.apellido }}, {{ deudor.nombre }}</strong>
                  <small>DNI {{ deudor.dni || 'sin informar' }} · Legajo {{ deudor.legajo || 'sin informar' }}</small>
                  <small v-if="deudor.telefono || deudor.email">{{ deudor.telefono || 'Sin teléfono' }} · {{ deudor.email || 'Sin email' }}</small>
                </td>
                <td>
                  <strong>{{ deudor.sucursal_nombre || 'Sin sucursal' }}</strong>
                  <small>{{ deudor.carrera_nombre || 'Sin carrera asignada' }}</small>
                </td>
                <td><strong class="debtors-debt">$ {{ formatMoney(deudor.deuda_total, { fractionDigits: 2 }) }}</strong></td>
                <td>
                  <strong>{{ deudor.cuotas_pendientes }}</strong>
                  <small>{{ deudor.cuotas_vencidas }} vencidas</small>
                </td>
                <td>{{ deudor.cuota_vencida_mas_antigua ? `${formatDate(deudor.cuota_vencida_mas_antigua)} · ${deudor.dias_mora} días` : 'Sin vencidas' }}</td>
                <td>{{ deudor.fecha_ultimo_pago ? formatDate(deudor.fecha_ultimo_pago) : 'Sin pagos' }}</td>
                <td>
                  <div class="users-row-actions debtors-actions">
                    <button type="button" @click="openEstado(deudor)">Estado de cuenta</button>
                    <button v-if="canRegisterPayments" type="button" @click="openPago(deudor)">Registrar pago</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="deudores.length" class="mobile-record-list debtors-mobile-list" role="list">
          <article v-for="deudor in deudores" :key="`mobile-${deudor.id}`" class="mobile-record-card" role="listitem">
            <header class="mobile-record-head"><span class="mobile-record-title"><strong>{{ deudor.apellido }}, {{ deudor.nombre }}</strong><small>{{ deudor.legajo }} · {{ deudor.sucursal_nombre }}</small></span><strong class="debtors-debt">$ {{ formatMoney(deudor.deuda_total, { fractionDigits: 2 }) }}</strong></header>
            <dl class="mobile-record-meta"><div><dt>Cuotas</dt><dd>{{ deudor.cuotas_pendientes }} pendientes · {{ deudor.cuotas_vencidas }} vencidas</dd></div><div><dt>Antigüedad</dt><dd>{{ deudor.dias_mora ? `${deudor.dias_mora} días` : 'Sin vencidas' }}</dd></div><div><dt>Contacto</dt><dd>{{ deudor.telefono || deudor.email || 'Sin informar' }}</dd></div></dl>
            <footer class="mobile-record-footer debtors-mobile-actions"><button type="button" @click="openEstado(deudor)">Estado de cuenta</button><button v-if="canRegisterPayments" type="button" @click="openPago(deudor)">Registrar pago</button></footer>
          </article>
        </div>
      </section>

      <p v-if="error" class="students-inline-error" role="alert">{{ error }}</p>

      <nav class="students-pagination" aria-label="Paginación de deudores">
        <label class="students-page-size">
          <span>Mostrar</span>
          <select v-model="pageSize" aria-label="Cantidad de deudores por página">
            <option v-for="option in pageSizeOptions" :key="option" :value="option">{{ option }}</option>
          </select>
          <span>por página</span>
        </label>
        <button type="button" :disabled="loading || pagination.page <= 1" @click="goToPage(pagination.page - 1)">Anterior</button>
        <span aria-live="polite">Página {{ pagination.page }} de {{ totalPages }} · {{ pagination.count }} deudores</span>
        <button type="button" :disabled="loading || pagination.page >= totalPages" @click="goToPage(pagination.page + 1)">Siguiente</button>
      </nav>

      <EstadoCuentaModal :open="showEstadoCuenta" :alumno="selectedAlumno" @close="showEstadoCuenta = false" />
      <PagoForm
        :open="showPagoForm"
        :alumno="selectedAlumno"
        :conceptos="conceptos"
        @close="showPagoForm = false"
        @saved="onPagoSaved"
      />
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  BanknotesIcon,
  BuildingStorefrontIcon,
  ChevronDownIcon,
  ExclamationCircleIcon,
  MagnifyingGlassIcon,
  ArrowDownTrayIcon,
} from '@heroicons/vue/24/outline'
import AppPageState from '@/components/ui/AppPageState.vue'
import EstadoCuentaModal from '@/components/alumnos/EstadoCuentaModal.vue'
import PagoForm from '@/components/alumnos/PagoForm.vue'
import { useCatalogos } from '@/composables/useCatalogos'
import { useDeudores } from '@/composables/useDeudores'
import { useAuth } from '@/composables/useAuth'
import { useToast } from '@/composables/useToast'
import { formatDate, formatMoney } from '@/lib/formatters'
import { useReportes } from '@/composables/useReportes'

const { sucursales, carreras, conceptos, loadCatalogos } = useCatalogos()
const { deudores, pagination, loading, error, loadDeudores } = useDeudores()
const auth = useAuth()
const toast = useToast()
const { exportarExcel } = useReportes()

const search = ref('')
const sucursalFilter = ref('todas')
const carreraFilter = ref('')
const onlyOverdue = ref(false)
const deudaMin = ref('')
const deudaMax = ref('')
const ordering = ref('deuda')
const periodo = ref('')
const segmento = ref('')
const pageSize = ref(10)
const currentPage = ref(1)
const pageSizeOptions = [5, 10, 25]
const pageReady = ref(false)
const pageError = ref('')
const selectedAlumno = ref(null)
const showEstadoCuenta = ref(false)
const showPagoForm = ref(false)

const canRegisterPayments = computed(() => auth.can('register-payments'))
const careerOptions = computed(() => carreras.value.filter((carrera) => (
  sucursalFilter.value === 'todas' || String(carrera.sucursal) === String(sucursalFilter.value)
)))
const totalPages = computed(() => Math.max(1, Math.ceil(pagination.value.count / pagination.value.pageSize)))

function buildQuery() {
  return {
    page: currentPage.value,
    page_size: pageSize.value,
    search: search.value.trim(),
    sucursal: sucursalFilter.value === 'todas' ? '' : sucursalFilter.value,
    carrera: carreraFilter.value,
    vencidas: onlyOverdue.value ? '1' : '',
    deuda_min: deudaMin.value,
    deuda_max: deudaMax.value,
    orden: ordering.value,
    periodo: periodo.value,
    segmento: segmento.value,
  }
}

async function loadPage() {
  pageReady.value = false
  pageError.value = ''
  try {
    await Promise.all([loadCatalogos(), loadDeudores(buildQuery())])
    pageReady.value = true
  } catch (err) {
    pageError.value = err.message || 'No se pudo cargar la cartera de deudores.'
  }
}

async function loadFilteredPage() {
  try {
    await loadDeudores(buildQuery())
  } catch (err) {
    toast.error(err.message || 'No se pudo actualizar la cartera de deudores.')
  }
}

watch(
  [search, sucursalFilter, carreraFilter, onlyOverdue, deudaMin, deudaMax, ordering, periodo, segmento, pageSize],
  (_, __, onCleanup) => {
    currentPage.value = 1
    const timer = setTimeout(() => loadFilteredPage(), 250)
    onCleanup(() => clearTimeout(timer))
  },
)

watch(sucursalFilter, () => {
  if (carreraFilter.value && !careerOptions.value.some((carrera) => String(carrera.id) === String(carreraFilter.value))) {
    carreraFilter.value = ''
  }
})

async function goToPage(page) {
  if (page < 1 || page > totalPages.value || page === pagination.value.page) return
  currentPage.value = page
  await loadFilteredPage()
}

function openEstado(deudor) {
  selectedAlumno.value = deudor
  showEstadoCuenta.value = true
}

function openPago(deudor) {
  if (!canRegisterPayments.value) return
  selectedAlumno.value = deudor
  showPagoForm.value = true
}

async function onPagoSaved() {
  showPagoForm.value = false
  await loadFilteredPage()
}

async function exportDebt() {
  try {
    await exportarExcel('morosidad', buildQuery())
    toast.success('Reporte de morosidad descargado')
  } catch (err) {
    toast.error(err.message || 'No se pudo exportar la morosidad.')
  }
}

onMounted(loadPage)
</script>

<style scoped>
.debtors-toolbar {
  align-items: flex-start;
}

.debtors-filters {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 9px;
}

.debtors-filter-field,
.debtors-order-field,
.debtors-amount-field {
  height: 44px;
  display: flex;
  align-items: center;
}

.debtors-filter-field select,
.debtors-filter-field input,
.debtors-order-field select,
.debtors-amount-field input {
  width: 154px;
  height: 100%;
  padding: 0 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-primary);
  background: var(--surface);
  font-size: 12px;
}

.debtors-export { display: inline-flex; align-items: center; gap: .4rem; min-height: 44px; border: 1px solid var(--primary); border-radius: 10px; padding: 0 .8rem; background: transparent; color: var(--primary); font-weight: 800; }
.debtors-export svg { width: 1.1rem; }
.debtors-mobile-list { display: none; }

.debtors-order-field select {
  width: 145px;
}

.debtors-amount-field input {
  width: 112px;
}

.debtors-summary {
  display: flex;
  align-items: baseline;
  gap: 7px;
  padding: 13px 18px;
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 12px;
}

.debtors-summary strong {
  color: var(--primary);
  font-size: 20px;
}

.debtors-table-wrap {
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 16px;
}

.debtors-table td {
  vertical-align: top;
}

.debtors-table td strong,
.debtors-table td small {
  display: block;
}

.debtors-table td small {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 11px;
}

.debtors-debt {
  color: var(--danger);
  white-space: nowrap;
}

.debtors-actions {
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
}

.debtors-actions button {
  white-space: nowrap;
}

.debtors-loading,
.debtors-empty {
  min-height: 220px;
  display: grid;
  place-content: center;
  text-align: center;
  color: var(--text-secondary);
}

@media (max-width: 1180px) {
  .debtors-toolbar {
    flex-direction: column;
  }

  .debtors-filters {
    justify-content: flex-start;
  }
}

@media (max-width: 820px) {
  .debtors-table-wrap .users-table-wrap { display: none; }
  .debtors-mobile-list { display: grid; gap: .75rem; padding: .75rem; }
  .debtors-mobile-actions { display: grid; grid-template-columns: 1fr 1fr; gap: .5rem; }
  .debtors-mobile-actions button { min-height: 42px; border: 1px solid var(--border); border-radius: .6rem; background: var(--surface); color: var(--primary); font-weight: 800; }

  .debtors-filters,
  .debtors-filters > * {
    width: 100%;
  }

  .debtors-search-field,
  .debtors-filter-field select,
  .debtors-filter-field input,
  .debtors-order-field select,
  .debtors-amount-field input {
    width: 100%;
  }
}
</style>
