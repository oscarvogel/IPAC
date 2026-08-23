<template>
  <section class="students-screen text-text-primary">
    <AppPageState
      v-if="!pageReady"
      :loading="!pageError"
      :error="pageError"
      label="los alumnos"
      @retry="loadPage"
    />
    <template v-else>
    <div class="students-stats">
      <article
        v-for="stat in stats"
        :key="stat.label"
        class="students-stat-card border-border bg-surface"
      >
        <span class="students-stat-icon" :class="`students-stat-icon-${stat.tone}`">
          <component :is="stat.icon" aria-hidden="true" />
        </span>
        <span class="students-stat-copy">
          <span>{{ stat.label }}</span>
          <strong>{{ stat.value }}</strong>
          <small>{{ stat.detail }}</small>
        </span>
      </article>
    </div>

    <section class="students-toolbar border-border bg-surface" aria-label="Filtros de alumnos">
      <div class="students-toolbar-heading">
        <span class="students-toolbar-icon">
          <UserGroupIcon aria-hidden="true" />
        </span>
        <div>
          <p class="eyebrow">Gestión académica</p>
          <h2>Directorio de alumnos</h2>
          <p>Encontrá y administrá cada legajo desde un solo lugar.</p>
        </div>
      </div>

      <div class="students-filters">
        <label class="students-search-field">
          <MagnifyingGlassIcon aria-hidden="true" />
          <span class="sr-only">Buscar alumno</span>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Buscar por nombre, apellido, DNI o legajo"
          />
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

        <label class="students-branch-field">
          <AcademicCapIcon aria-hidden="true" />
          <span class="sr-only">Filtrar por carrera o curso</span>
          <select v-model="carreraFilter">
            <option value="todas">Todas las carreras</option>
            <option v-for="carrera in availableCareers" :key="carrera.id" :value="carrera.id">
              {{ carrera.nombre }}
            </option>
          </select>
          <ChevronDownIcon class="students-select-chevron" aria-hidden="true" />
        </label>

        <label class="students-branch-field">
          <CheckIcon aria-hidden="true" />
          <span class="sr-only">Filtrar por estado</span>
          <select v-model="estadoFilter">
            <option value="todos">Todos los estados</option>
            <option value="activo">Activos</option>
            <option value="inactivo">Inactivos</option>
            <option value="baja">Dados de baja</option>
          </select>
          <ChevronDownIcon class="students-select-chevron" aria-hidden="true" />
        </label>

        <label class="students-branch-field">
          <BanknotesIcon aria-hidden="true" />
          <span class="sr-only">Filtrar por situación financiera</span>
          <select v-model="financialFilter">
            <option value="todos">Cualquier situación financiera</option>
            <option value="deuda">Con deuda</option>
            <option value="saldo">Con saldo a favor</option>
          </select>
          <ChevronDownIcon class="students-select-chevron" aria-hidden="true" />
        </label>

        <button
          v-if="canManageAlumnos"
          type="button"
          class="students-primary-action bg-primary hover:bg-primary-hover"
          @click="openNewAlumnoForm"
        >
          <UserPlusIcon aria-hidden="true" />
          <span>Nuevo alumno</span>
        </button>
        <button
          v-if="canManageFees"
          type="button"
          class="students-primary-action bg-primary hover:bg-primary-hover"
          @click="openGenerarCuotasMasivas"
        >
          <UserPlusIcon aria-hidden="true" />
          <span>Generar cuotas masivas</span>
        </button>
      </div>
      <div v-if="activeFilterChips.length" class="students-filter-chips" aria-label="Filtros activos">
        <span>Filtros activos:</span>
        <button
          v-for="chip in activeFilterChips"
          :key="chip.id"
          type="button"
          :aria-label="`Quitar filtro ${chip.label}`"
          @click="clearFilter(chip.id)"
        >
          {{ chip.label }} <span aria-hidden="true">×</span>
        </button>
        <button type="button" class="clear-all" @click="clearAllFilters">Limpiar todos</button>
      </div>
    </section>

    <div class="students-grid">
      <AlumnoList
        :alumnos="visibleAlumnos"
        :selected-alumno="selectedAlumno"
        :filtered="hasActiveFilters"
        :total-count="pagination.count"
        @select="onSelect"
      />
      <AlumnoDetail
        :alumno="selectedAlumno"
        :conceptos="conceptos"
        :pagos="pagos"
        :can-edit="canManageAlumnos"
        :can-register-pago="canRegisterPayments"
        :can-generate-fee="canManageFees"
        :can-toggle-state="canManageAlumnos"
        :can-manage-matriculas="canManageAlumnos"
        @register-pago="openPagoForm"
        @edit="openEditForm"
        @view-estado="openEstadoCuenta"
        @generar-cuota="openGenerarCuota"
        @toggle-estado="handleToggleEstado"
        @matricula-changed="onMatriculaChanged"
      />
    </div>

    <p v-if="alumnosError" class="students-inline-error" role="alert">{{ alumnosError }}</p>

    <nav
      class="students-pagination"
      aria-label="Paginación de alumnos"
    >
      <label class="students-page-size">
        <span>Mostrar</span>
        <select v-model="pageSize" aria-label="Cantidad de alumnos por página">
          <option v-for="option in pageSizeOptions" :key="option" :value="option">
            {{ option }}
          </option>
        </select>
        <span>por página</span>
      </label>
      <button
        type="button"
        :disabled="alumnosLoading || pagination.page <= 1"
        @click="goToPage(pagination.page - 1)"
      >
        Anterior
      </button>
      <span aria-live="polite">
        Página {{ pagination.page }} de {{ totalPages }} · {{ pagination.count }} alumnos
      </span>
      <button
        type="button"
        :disabled="alumnosLoading || pagination.page >= totalPages"
        @click="goToPage(pagination.page + 1)"
      >
        Siguiente
      </button>
    </nav>

    <AlumnoForm
      :open="showAlumnoForm"
      :alumno="editingAlumno"
      @close="closeAlumnoForm"
      @saved="onAlumnoSaved"
    />

    <PagoForm
      :open="showPagoForm"
      :alumno="selectedAlumno"
      :conceptos="conceptos"
      @close="closePagoForm"
      @saved="onPagoSaved"
    />

    <EstadoCuentaModal
      :open="showEstadoCuenta"
      :alumno="selectedAlumno"
      @close="closeEstadoCuenta"
    />

    <GenerarCuotaModal
      :open="showGenerarCuota"
      :alumno="selectedAlumno"
      :conceptos="conceptos"
      @close="showGenerarCuota = false"
      @saved="onCuotaGenerada"
    />

    <GenerarCuotasMasivasModal
      :open="showGenerarCuotasMasivas"
      :sucursales="sucursales"
      :carreras="carreras"
      :conceptos="conceptos"
      @close="showGenerarCuotasMasivas = false"
      @saved="onCuotasMasivasSaved"
    />

    <ConfirmDialog
      :open="Boolean(pendingDeactivateAlumno)"
      title="Dar de baja al alumno"
      description="El legajo dejará de estar activo, pero conservará su información y estado de cuenta."
      :subject="pendingDeactivateAlumno ? `${pendingDeactivateAlumno.nombre} ${pendingDeactivateAlumno.apellido}` : ''"
      confirm-label="Dar de baja"
      :loading="changingAlumnoStatus"
      @cancel="pendingDeactivateAlumno = null"
      @confirm="confirmDeactivateAlumno"
    />
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AcademicCapIcon,
  BanknotesIcon,
  BuildingStorefrontIcon,
  CheckCircleIcon,
  CheckIcon,
  ChevronDownIcon,
  MagnifyingGlassIcon,
  PauseCircleIcon,
  UserGroupIcon,
  UserPlusIcon,
} from '@heroicons/vue/24/outline'
import { useAlumnos } from '@/composables/useAlumnos'
import { useCatalogos } from '@/composables/useCatalogos'
import { usePagos } from '@/composables/usePagos'
import { useToast } from '@/composables/useToast'
import { useAuth } from '@/composables/useAuth'
import AlumnoList from '@/components/alumnos/AlumnoList.vue'
import AlumnoDetail from '@/components/alumnos/AlumnoDetail.vue'
import AlumnoForm from '@/components/alumnos/AlumnoForm.vue'
import PagoForm from '@/components/alumnos/PagoForm.vue'
import EstadoCuentaModal from '@/components/alumnos/EstadoCuentaModal.vue'
import GenerarCuotaModal from '@/components/alumnos/GenerarCuotaModal.vue'
import GenerarCuotasMasivasModal from '@/components/alumnos/GenerarCuotasMasivasModal.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import AppPageState from '@/components/ui/AppPageState.vue'

const {
  alumnos,
  selectedAlumno,
  pagination,
  alumnoStats,
  loading: alumnosLoading,
  error: alumnosError,
  setSelected,
  loadAlumnos,
  loadAlumnoStats,
  deactivateAlumno,
  reactivateAlumno,
} = useAlumnos()
const toast = useToast()
const auth = useAuth()
const route = useRoute()
const router = useRouter()
const canManageAlumnos = computed(() => auth.can('manage-alumnos'))
const canRegisterPayments = computed(() => auth.can('register-payments'))
const canManageFees = computed(() => auth.can('manage-fees'))
const { sucursales, carreras, conceptos, loadCatalogos } = useCatalogos()
const { pagos, loadPagos } = usePagos()

const searchQuery = ref('')
const sucursalFilter = ref('todas')
const carreraFilter = ref('todas')
const estadoFilter = ref('todos')
const financialFilter = ref('todos')
const pageSize = ref(10)
const pageSizeOptions = [5, 10, 25]
const currentPage = ref(1)

const showAlumnoForm = ref(false)
const editingAlumno = ref(null)
const showPagoForm = ref(false)
const showEstadoCuenta = ref(false)
const showGenerarCuota = ref(false)
const showGenerarCuotasMasivas = ref(false)
const pendingDeactivateAlumno = ref(null)
const changingAlumnoStatus = ref(false)
const pageReady = ref(false)
const pageError = ref('')

onMounted(loadPage)

watch(
  [pageReady, () => route.query.accion],
  ([ready, accion]) => {
    if (!ready || !accion) return
    consumeRouteAction(accion)
  },
  { immediate: true },
)

watch(
  [searchQuery, sucursalFilter, carreraFilter, estadoFilter, financialFilter, pageSize],
  (_, __, onCleanup) => {
    currentPage.value = 1
    const timer = setTimeout(() => {
      loadStudentsPage()
    }, 250)
    onCleanup(() => clearTimeout(timer))
  },
)

const totalPages = computed(() => Math.max(1, Math.ceil(pagination.value.count / pagination.value.pageSize)))

function studentQuery() {
  return {
    page: currentPage.value,
    page_size: pageSize.value,
    search: searchQuery.value.trim(),
    sucursal: sucursalFilter.value === 'todas' ? '' : sucursalFilter.value,
    carrera: carreraFilter.value === 'todas' ? '' : carreraFilter.value,
    estado: estadoFilter.value === 'todos' ? '' : estadoFilter.value,
    con_deuda: financialFilter.value === 'deuda' ? '1' : '',
    con_saldo_favor: financialFilter.value === 'saldo' ? '1' : '',
  }
}

async function loadStudentsPage() {
  const query = studentQuery()
  await Promise.all([loadAlumnos(query), loadAlumnoStats(query)])
  if (alumnosError.value) toast.error(alumnosError.value)
}

async function goToPage(page) {
  if (page < 1 || page > totalPages.value || page === pagination.value.page) return
  currentPage.value = page
  await loadStudentsPage()
}

async function loadPage() {
  pageReady.value = false
  pageError.value = ''
  try {
    const query = studentQuery()
    await Promise.all([loadCatalogos(), loadAlumnos(query), loadAlumnoStats(query)])
    await loadPagos(selectedAlumno.value ? { alumno: selectedAlumno.value.id } : {})
    if (alumnosError.value) throw new Error(alumnosError.value)
    pageReady.value = true
  } catch (err) {
    pageError.value = err.message || 'No se pudo cargar el directorio de alumnos.'
  }
}

async function onSelect(alumno) {
  setSelected(alumno.id)
  await loadPagos({ alumno: alumno.id })
}

function openNewAlumnoForm() {
  editingAlumno.value = null
  showAlumnoForm.value = true
}

function openEditForm() {
  editingAlumno.value = selectedAlumno.value
  showAlumnoForm.value = true
}

function closeAlumnoForm() {
  showAlumnoForm.value = false
  editingAlumno.value = null
}

function onAlumnoSaved(saved) {
  setSelected(saved.id)
  loadStudentsPage()
}

function openPagoForm() {
  if (!selectedAlumno.value) return
  showPagoForm.value = true
}

function closePagoForm() {
  showPagoForm.value = false
}

async function onPagoSaved() {
  if (selectedAlumno.value) await loadPagos({ alumno: selectedAlumno.value.id })
  await loadStudentsPage()
}

function openEstadoCuenta() {
  if (!selectedAlumno.value) return
  showEstadoCuenta.value = true
}

function closeEstadoCuenta() {
  showEstadoCuenta.value = false
}

function openGenerarCuota() {
  if (!canManageFees.value || !selectedAlumno.value) return
  showGenerarCuota.value = true
}

async function onMatriculaChanged() {
  await loadStudentsPage()
}

async function onCuotaGenerada() {
  showGenerarCuota.value = false
  if (selectedAlumno.value) await loadPagos({ alumno: selectedAlumno.value.id })
  await loadStudentsPage()
}

function openGenerarCuotasMasivas() {
  if (canManageFees.value) showGenerarCuotasMasivas.value = true
}

function consumeRouteAction(accion) {
  const { accion: _discarded, ...query } = route.query
  router.replace({ path: route.path, query, hash: route.hash })

  if (accion === 'nuevo' && canManageAlumnos.value) {
    openNewAlumnoForm()
  } else if (accion === 'cuotas-masivas' && canManageFees.value) {
    openGenerarCuotasMasivas()
  }
}

function onCuotasMasivasSaved() {
  showGenerarCuotasMasivas.value = false
}

async function handleToggleEstado(alumno) {
  if (alumno.estado !== 'inactivo') {
    pendingDeactivateAlumno.value = alumno
    return
  }

  try {
    await reactivateAlumno(alumno.id)
    await loadStudentsPage()
    toast.success('Alumno reactivado')
  } catch (err) {
    toast.error(err.message || 'Error al cambiar estado del alumno')
  }
}

async function confirmDeactivateAlumno() {
  if (!pendingDeactivateAlumno.value) return
  changingAlumnoStatus.value = true
  try {
    await deactivateAlumno(pendingDeactivateAlumno.value.id)
    await loadStudentsPage()
    toast.success('Alumno dado de baja')
    pendingDeactivateAlumno.value = null
  } catch (err) {
    toast.error(err.message || 'Error al cambiar estado del alumno')
  } finally {
    changingAlumnoStatus.value = false
  }
}

const visibleAlumnos = computed(() => alumnos.value)

const hasActiveFilters = computed(() => Boolean(
  searchQuery.value.trim()
  || sucursalFilter.value !== 'todas'
  || carreraFilter.value !== 'todas'
  || estadoFilter.value !== 'todos'
  || financialFilter.value !== 'todos',
))

const availableCareers = computed(() => carreras.value.filter((carrera) => (
  sucursalFilter.value === 'todas'
  || String(carrera.sucursal) === String(sucursalFilter.value)
)))

const activeFilterChips = computed(() => {
  const chips = []
  if (searchQuery.value.trim()) chips.push({ id: 'search', label: `Búsqueda: ${searchQuery.value.trim()}` })
  if (sucursalFilter.value !== 'todas') {
    const item = sucursales.value.find((sucursal) => String(sucursal.id) === String(sucursalFilter.value))
    chips.push({ id: 'sucursal', label: item?.nombre || 'Sucursal' })
  }
  if (carreraFilter.value !== 'todas') {
    const item = carreras.value.find((carrera) => String(carrera.id) === String(carreraFilter.value))
    chips.push({ id: 'carrera', label: item?.nombre || 'Carrera' })
  }
  if (estadoFilter.value !== 'todos') {
    chips.push({ id: 'estado', label: { activo: 'Activos', inactivo: 'Inactivos', baja: 'Dados de baja' }[estadoFilter.value] })
  }
  if (financialFilter.value !== 'todos') {
    chips.push({ id: 'financiero', label: financialFilter.value === 'deuda' ? 'Con deuda' : 'Con saldo a favor' })
  }
  return chips
})

function clearFilter(id) {
  if (id === 'search') searchQuery.value = ''
  if (id === 'sucursal') sucursalFilter.value = 'todas'
  if (id === 'carrera') carreraFilter.value = 'todas'
  if (id === 'estado') estadoFilter.value = 'todos'
  if (id === 'financiero') financialFilter.value = 'todos'
}

function clearAllFilters() {
  searchQuery.value = ''
  sucursalFilter.value = 'todas'
  carreraFilter.value = 'todas'
  estadoFilter.value = 'todos'
  financialFilter.value = 'todos'
}

const selectedBranchName = computed(() => {
  if (sucursalFilter.value === 'todas') return 'en toda la institución'
  const branch = sucursales.value.find(
    (sucursal) => String(sucursal.id) === String(sucursalFilter.value),
  )
  return branch ? `en ${branch.nombre}` : 'en la sucursal seleccionada'
})

const stats = computed(() => [
  {
    label: 'Total de alumnos',
    value: pagination.value.count,
    detail: selectedBranchName.value,
    tone: 'primary',
    icon: UserGroupIcon,
  },
  {
    label: 'Alumnos activos',
    value: alumnoStats.value.activos,
    detail: 'legajos activos',
    tone: 'success',
    icon: CheckCircleIcon,
  },
  {
    label: 'Inactivos',
    value: alumnoStats.value.inactivos,
    detail: 'legajos en pausa o baja',
    tone: 'warning',
    icon: PauseCircleIcon,
  },
  {
    label: 'Sucursales',
    value: sucursales.value.length,
    detail: 'sedes disponibles',
    tone: 'info',
    icon: BuildingStorefrontIcon,
  },
])
</script>

<style scoped>
.students-filter-chips { padding-top: .65rem; display: flex; align-items: center; flex-wrap: wrap; gap: .4rem; border-top: 1px solid var(--border); color: var(--text-secondary); font-size: .78rem; font-weight: 700; }
.students-filter-chips button { min-height: 2rem; border: 1px solid var(--border); border-radius: 999px; padding: 0 .7rem; background: var(--primary-soft); color: var(--primary); font-size: .75rem; font-weight: 800; }
.students-filter-chips button.clear-all { background: transparent; color: var(--text-secondary); }
</style>
