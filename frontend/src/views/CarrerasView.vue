<template>
  <section class="careers-workspace">
    <AppPageState
      v-if="!pageReady"
      :loading="!pageError"
      :error="pageError"
      label="las carreras"
      @retry="loadPage"
    />
    <template v-else>
      <div class="careers-metrics-grid">
        <article
          v-for="stat in stats"
          :key="stat.label"
          class="careers-metric-card border-border bg-surface"
        >
          <span class="careers-metric-icon" :class="`careers-metric-icon-${stat.tone}`">
            <component :is="stat.icon" aria-hidden="true" />
          </span>
          <span class="careers-metric-copy">
            <span>{{ stat.label }}</span>
            <strong>{{ stat.value }}</strong>
            <small>{{ stat.detail }}</small>
          </span>
        </article>
      </div>

      <section v-if="sinDesglose.length" class="careers-alert" role="status">
        <ExclamationTriangleIcon aria-hidden="true" />
        <div>
          <strong>
            {{ sinDesglose.length }}
            {{ sinDesglose.length === 1 ? 'carrera sin desglose' : 'carreras sin desglose' }}
          </strong>
          <p>
            Sus recibos se emiten sin el reparto programático y extraprogramático que pide el
            Ministerio de Educación. Cargá las dos partes de la cuota.
          </p>
        </div>
        <button type="button" @click="abrirPrimeraSinDesglose">
          <span>Corregir ahora</span>
          <ChevronRightIcon aria-hidden="true" />
        </button>
      </section>

      <section class="careers-toolbar border-border bg-surface" aria-label="Filtros de carreras">
        <div class="careers-toolbar-heading">
          <span class="careers-toolbar-icon">
            <AcademicCapIcon aria-hidden="true" />
          </span>
          <div>
            <p class="eyebrow">Gestión de trayectoria</p>
            <h2>Catálogo de carreras y cursos</h2>
            <p>Planes de estudio, planes de cuotas y desglose de importes.</p>
          </div>
        </div>

        <div class="careers-filters">
          <label class="careers-search-field">
            <MagnifyingGlassIcon aria-hidden="true" />
            <span class="sr-only">Buscar carrera o curso</span>
            <input v-model="searchQuery" type="search" placeholder="Buscar carrera o curso" />
          </label>

          <label class="careers-branch-field">
            <BuildingStorefrontIcon aria-hidden="true" />
            <span class="sr-only">Filtrar por sucursal</span>
            <select v-model="sucursalFilter">
              <option value="todas">Todas las sucursales</option>
              <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
                {{ sucursal.nombre }}
              </option>
            </select>
            <ChevronDownIcon class="careers-select-chevron" aria-hidden="true" />
          </label>

          <label class="careers-branch-field">
            <span class="sr-only">Filtrar por tipo</span>
            <select v-model="tipoFilter">
              <option value="todos">Carreras y cursos</option>
              <option value="carrera">Solo carreras</option>
              <option value="curso">Solo cursos</option>
            </select>
            <ChevronDownIcon class="careers-select-chevron" aria-hidden="true" />
          </label>

          <label class="careers-active-filter" :class="{ active: onlyActive }">
            <input v-model="onlyActive" class="sr-only" type="checkbox" />
            <CheckIcon aria-hidden="true" />
            <span>Solo activas</span>
          </label>

          <button
            type="button"
            v-if="canManageCareers"
            class="careers-primary-action bg-primary hover:bg-primary-hover"
            @click="openNewCarreraForm"
          >
            <PlusIcon aria-hidden="true" />
            <span>Nueva carrera</span>
          </button>
        </div>
      </section>

      <CarreraList
        :carreras="filteredCarreras"
        :filtered="hasActiveFilters"
        :can-edit="canManageCareers"
        :can-deactivate="canManageCareers"
        :animate="listMotionEnabled"
        @edit="openEditForm"
        @deactivate="requestDeactivate"
      />

      <CarreraForm
        :open="showCarreraForm"
        :carrera="editingCarrera"
        @close="closeCarreraForm"
        @saved="onCarreraSaved"
      />

      <ConfirmDialog
        :open="Boolean(pendingDeactivateCarrera)"
        title="Desactivar carrera"
        description="La carrera dejará de estar disponible para nuevas matrículas y generación de cuotas. Los registros existentes no se modifican."
        :subject="pendingDeactivateCarrera?.nombre || ''"
        confirm-label="Desactivar"
        :loading="deactivatingCarrera"
        @cancel="pendingDeactivateCarrera = null"
        @confirm="confirmDeactivate"
      />
    </template>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  AcademicCapIcon,
  BuildingStorefrontIcon,
  CheckCircleIcon,
  CheckIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  Squares2X2Icon,
} from '@heroicons/vue/24/outline'
import { useCatalogos } from '@/composables/useCatalogos'
import { useCarreras } from '@/composables/useCarreras'
import { useToast } from '@/composables/useToast'
import { useAuth } from '@/composables/useAuth'
import CarreraList from '@/components/carreras/CarreraList.vue'
import CarreraForm from '@/components/carreras/CarreraForm.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import AppPageState from '@/components/ui/AppPageState.vue'

const { sucursales, loadCatalogo, loadCatalogos } = useCatalogos()
const { carreras, error: carrerasError, loadCarreras, deactivateCarrera } = useCarreras()
const toast = useToast()
const auth = useAuth()
const canManageCareers = computed(() => auth.can('manage-careers'))

const searchQuery = ref('')
const sucursalFilter = ref('todas')
const tipoFilter = ref('todos')
const onlyActive = ref(false)

const showCarreraForm = ref(false)
const editingCarrera = ref(null)
const pendingDeactivateCarrera = ref(null)
const deactivatingCarrera = ref(false)
const pageReady = ref(false)
const pageError = ref('')
const listMotionEnabled = ref(true)
let searchMotionTimer = null

onMounted(loadPage)

watch(searchQuery, () => {
  listMotionEnabled.value = false
  if (searchMotionTimer) clearTimeout(searchMotionTimer)
  searchMotionTimer = setTimeout(() => {
    listMotionEnabled.value = true
    searchMotionTimer = null
  }, 280)
})

onBeforeUnmount(() => {
  if (searchMotionTimer) clearTimeout(searchMotionTimer)
})

async function loadPage() {
  pageReady.value = false
  pageError.value = ''
  try {
    await Promise.all([
      loadCatalogo?.('sucursales') || loadCatalogos(),
      loadCarreras(),
    ])
    if (carrerasError.value) throw new Error(carrerasError.value)
    pageReady.value = true
  } catch (err) {
    pageError.value = err.message || 'No se pudo cargar el catálogo de carreras.'
  }
}

function tieneDesglose(carrera) {
  const vacio = (valor) => valor === null || valor === undefined || valor === ''
  return !vacio(carrera.cuota_programatica) && !vacio(carrera.cuota_extraprogramatica)
}

const branchCarreras = computed(() => {
  if (sucursalFilter.value === 'todas') return carreras.value
  return carreras.value.filter(
    (carrera) => String(carrera.sucursal) === String(sucursalFilter.value),
  )
})

const sinDesglose = computed(() => branchCarreras.value.filter((carrera) => !tieneDesglose(carrera)))

const filteredCarreras = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return branchCarreras.value.filter((carrera) => {
    const matchesActive = !onlyActive.value || carrera.activa
    const matchesTipo = tipoFilter.value === 'todos' || carrera.tipo === tipoFilter.value
    const text = [carrera.nombre, carrera.tipo, carrera.sucursal_nombre, carrera.duracion]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    const matchesQuery = !query || text.includes(query)
    return matchesActive && matchesTipo && matchesQuery
  })
})

const hasActiveFilters = computed(() => Boolean(
  searchQuery.value.trim()
  || sucursalFilter.value !== 'todas'
  || tipoFilter.value !== 'todos'
  || onlyActive.value,
))

const totalActivas = computed(() => branchCarreras.value.filter((carrera) => carrera.activa).length)

const selectedBranchName = computed(() => {
  if (sucursalFilter.value === 'todas') return 'en toda la institución'
  const branch = sucursales.value.find(
    (sucursal) => String(sucursal.id) === String(sucursalFilter.value),
  )
  return branch ? `en ${branch.nombre}` : 'en la sucursal seleccionada'
})

const stats = computed(() => [
  {
    label: 'Total de carreras',
    value: branchCarreras.value.length,
    detail: selectedBranchName.value,
    tone: 'primary',
    icon: AcademicCapIcon,
  },
  {
    label: 'Carreras activas',
    value: totalActivas.value,
    detail: `${branchCarreras.value.length - totalActivas.value} inactivas`,
    tone: 'success',
    icon: CheckCircleIcon,
  },
  {
    label: 'Con desglose',
    value: branchCarreras.value.length - sinDesglose.value.length,
    detail: 'recibo con reparto programático',
    tone: 'info',
    icon: Squares2X2Icon,
  },
  {
    label: 'Sin desglose',
    value: sinDesglose.value.length,
    detail: 'recibo sin reparto programático',
    tone: 'warning',
    icon: ExclamationTriangleIcon,
  },
])

function abrirPrimeraSinDesglose() {
  const primera = sinDesglose.value[0]
  if (!primera) return
  openEditForm(primera)
}

function openNewCarreraForm() {
  editingCarrera.value = null
  showCarreraForm.value = true
}

function openEditForm(carrera) {
  editingCarrera.value = carrera
  showCarreraForm.value = true
}

function closeCarreraForm() {
  showCarreraForm.value = false
  editingCarrera.value = null
}

function onCarreraSaved() {
  closeCarreraForm()
}

function requestDeactivate(carrera) {
  pendingDeactivateCarrera.value = carrera
}

async function confirmDeactivate() {
  if (!pendingDeactivateCarrera.value) return
  deactivatingCarrera.value = true
  try {
    await deactivateCarrera(pendingDeactivateCarrera.value.id)
    toast.success('Carrera desactivada')
    pendingDeactivateCarrera.value = null
  } catch (err) {
    toast.error(err.message || 'No se pudo desactivar la carrera.')
  } finally {
    deactivatingCarrera.value = false
  }
}
</script>

<style scoped>
.careers-workspace {
  display: grid;
  gap: 1.5rem;
}

.careers-metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
  gap: 1rem;
}

.careers-metric-card {
  display: flex;
  gap: 0.85rem;
  align-items: center;
  padding: 1rem 1.15rem;
  border: 1px solid var(--border);
  border-radius: 0.9rem;
}

.careers-metric-icon {
  display: grid;
  place-items: center;
  width: 2.6rem;
  height: 2.6rem;
  flex: 0 0 auto;
  border-radius: 0.8rem;
  background: var(--primary-soft);
  color: var(--primary);
}

.careers-metric-icon svg {
  width: 1.3rem;
}

.careers-metric-icon-success {
  background: #dcfce7;
  color: #15803d;
}

.careers-metric-icon-info {
  background: #e0f2fe;
  color: #0369a1;
}

.careers-metric-icon-warning {
  background: #fff7ed;
  color: #9a3412;
}

.careers-metric-copy {
  display: grid;
  gap: 0.1rem;
}

.careers-metric-copy > span {
  color: var(--text-secondary);
  font-size: 0.78rem;
}

.careers-metric-copy strong {
  font-size: 1.35rem;
  line-height: 1.2;
}

.careers-metric-copy small {
  color: var(--text-secondary);
  font-size: 0.72rem;
}

.careers-alert {
  display: flex;
  gap: 0.85rem;
  align-items: center;
  flex-wrap: wrap;
  padding: 0.9rem 1.1rem;
  border: 1px solid #fed7aa;
  border-radius: 0.9rem;
  background: #fff7ed;
  color: #9a3412;
}

.careers-alert > svg {
  width: 1.4rem;
  flex: 0 0 auto;
}

.careers-alert strong {
  display: block;
  font-size: 0.9rem;
}

.careers-alert p {
  margin: 0.15rem 0 0;
  font-size: 0.82rem;
  max-width: 62ch;
}

.careers-alert button {
  display: inline-flex;
  gap: 0.3rem;
  align-items: center;
  margin-left: auto;
  min-height: 2.4rem;
  padding: 0.4rem 0.9rem;
  border: 1px solid #fdba74;
  border-radius: 0.6rem;
  background: var(--surface);
  color: #9a3412;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
}

.careers-alert button svg {
  width: 1rem;
}

.careers-toolbar {
  display: grid;
  gap: 1.1rem;
  padding: 1.15rem 1.25rem;
  border: 1px solid var(--border);
  border-radius: 14px;
}

.careers-toolbar-heading {
  display: flex;
  gap: 0.85rem;
  align-items: center;
}

.careers-toolbar-heading h2 {
  margin: 0.1rem 0 0.2rem;
  font-size: 1.05rem;
}

.careers-toolbar-heading p:last-child {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.careers-toolbar-icon {
  display: grid;
  place-items: center;
  width: 2.6rem;
  height: 2.6rem;
  flex: 0 0 auto;
  border-radius: 0.8rem;
  background: var(--primary-soft);
  color: var(--primary);
}

.careers-toolbar-icon svg {
  width: 1.35rem;
}

.careers-filters {
  display: flex;
  gap: 0.7rem;
  align-items: center;
  flex-wrap: wrap;
}

.careers-search-field,
.careers-branch-field {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 2.6rem;
  border: 1px solid var(--border);
  border-radius: 0.6rem;
  background: var(--surface);
  overflow: hidden;
}

.careers-search-field {
  flex: 1 1 16rem;
  min-width: 12rem;
}

.careers-branch-field {
  flex: 0 1 13rem;
}

.careers-search-field > svg {
  width: 1.05rem;
  margin-left: 0.7rem;
  color: var(--text-secondary);
}

.careers-search-field input,
.careers-branch-field select {
  width: 100%;
  min-height: 2.6rem;
  padding: 0 0.7rem;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
}

.careers-search-field input:focus-visible,
.careers-branch-field select:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: -2px;
}

.careers-branch-field select {
  appearance: none;
  padding-right: 2rem;
  cursor: pointer;
}

.careers-select-chevron {
  position: absolute;
  right: 0.6rem;
  width: 1rem;
  color: var(--text-secondary);
  pointer-events: none;
}

.careers-active-filter {
  display: inline-flex;
  gap: 0.35rem;
  align-items: center;
  min-height: 2.6rem;
  padding: 0 0.8rem;
  border: 1px solid var(--border);
  border-radius: 0.6rem;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
}

.careers-active-filter.active {
  border-color: var(--primary);
  color: var(--primary);
}

.careers-active-filter svg {
  width: 1rem;
}

.careers-primary-action {
  display: inline-flex;
  gap: 0.4rem;
  align-items: center;
  min-height: 2.6rem;
  margin-left: auto;
  padding: 0 1rem;
  border: 0;
  border-radius: 0.6rem;
  color: #fff;
  font-size: 0.87rem;
  font-weight: 600;
  cursor: pointer;
}

.careers-primary-action svg {
  width: 1.1rem;
}

@media (max-width: 640px) {
  .careers-primary-action {
    margin-left: 0;
    width: 100%;
    justify-content: center;
  }
}
</style>