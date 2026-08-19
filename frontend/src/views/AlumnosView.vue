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
        v-for="(stat, index) in stats"
        :key="stat.label"
        class="students-stat-card border-border bg-surface"
        :class="{ 'students-stat-card-featured': index === 0 }"
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

        <label class="students-active-filter" :class="{ active: onlyActive }">
          <input v-model="onlyActive" class="sr-only" type="checkbox" />
          <CheckIcon aria-hidden="true" />
          <span>Solo activos</span>
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
import {
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
const canManageAlumnos = computed(() => auth.can('manage-alumnos'))
const canRegisterPayments = computed(() => auth.can('register-payments'))
const canManageFees = computed(() => auth.can('manage-fees'))
const { sucursales, conceptos, loadCatalogos } = useCatalogos()
const { pagos, loadPagos } = usePagos()

const searchQuery = ref('')
const sucursalFilter = ref('todas')
const onlyActive = ref(false)
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
  [searchQuery, sucursalFilter, onlyActive, pageSize],
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
    estado: onlyActive.value ? 'activo' : '',
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
    await Promise.all([loadCatalogos(), loadAlumnos(query), loadAlumnoStats(query), loadPagos()])
    if (alumnosError.value) throw new Error(alumnosError.value)
    pageReady.value = true
  } catch (err) {
    pageError.value = err.message || 'No se pudo cargar el directorio de alumnos.'
  }
}

function onSelect(alumno) {
  setSelected(alumno.id)
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

function onPagoSaved() {
  // PagoForm ya recarga la lista. No hace falta hacer nada mas aca.
}

function openEstadoCuenta() {
  if (!selectedAlumno.value) return
  showEstadoCuenta.value = true
}

function closeEstadoCuenta() {
  showEstadoCuenta.value = false
}

async function onMatriculaChanged() {
  await loadStudentsPage()
}

function onCuotaGenerada() {
  showGenerarCuota.value = false
}

function openGenerarCuotasMasivas() {
  if (canManageFees.value) showGenerarCuotasMasivas.value = true
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
  || onlyActive.value,
))

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
</style>
