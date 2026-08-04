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
            placeholder="Buscar por nombre, DNI o legajo"
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
          type="button"
          class="students-primary-action bg-primary hover:bg-primary-hover"
          @click="openNewAlumnoForm"
        >
          <UserPlusIcon aria-hidden="true" />
          <span>Nuevo alumno</span>
        </button>
      </div>
    </section>

    <div class="students-grid">
      <AlumnoList
        :alumnos="visibleAlumnos"
        :selected-alumno="selectedAlumno"
        :filtered="hasActiveFilters"
        @select="onSelect"
      />
      <AlumnoDetail
        :alumno="selectedAlumno"
        :conceptos="conceptos"
        :pagos="pagos"
        @register-pago="openPagoForm"
        @edit="openEditForm"
        @view-estado="openEstadoCuenta"
        @generar-cuota="openGenerarCuota"
        @toggle-estado="handleToggleEstado"
      />
    </div>

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
import { computed, onMounted, ref } from 'vue'
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
import AlumnoList from '@/components/alumnos/AlumnoList.vue'
import AlumnoDetail from '@/components/alumnos/AlumnoDetail.vue'
import AlumnoForm from '@/components/alumnos/AlumnoForm.vue'
import PagoForm from '@/components/alumnos/PagoForm.vue'
import EstadoCuentaModal from '@/components/alumnos/EstadoCuentaModal.vue'
import GenerarCuotaModal from '@/components/alumnos/GenerarCuotaModal.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import AppPageState from '@/components/ui/AppPageState.vue'

const {
  alumnos,
  selectedAlumno,
  error: alumnosError,
  setSelected,
  loadAlumnos,
  deactivateAlumno,
  reactivateAlumno,
} = useAlumnos()
const toast = useToast()
const { sucursales, conceptos, loadCatalogos } = useCatalogos()
const { pagos, loadPagos } = usePagos()

const searchQuery = ref('')
const sucursalFilter = ref('todas')
const onlyActive = ref(false)

const showAlumnoForm = ref(false)
const editingAlumno = ref(null)
const showPagoForm = ref(false)
const showEstadoCuenta = ref(false)
const showGenerarCuota = ref(false)
const pendingDeactivateAlumno = ref(null)
const changingAlumnoStatus = ref(false)
const pageReady = ref(false)
const pageError = ref('')

onMounted(loadPage)

async function loadPage() {
  pageReady.value = false
  pageError.value = ''
  try {
    await Promise.all([loadCatalogos(), loadAlumnos(), loadPagos()])
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

function onCuotaGenerada() {
  showGenerarCuota.value = false
}

async function handleToggleEstado(alumno) {
  if (alumno.estado !== 'inactivo') {
    pendingDeactivateAlumno.value = alumno
    return
  }

  try {
    await reactivateAlumno(alumno.id)
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
    toast.success('Alumno dado de baja')
    pendingDeactivateAlumno.value = null
  } catch (err) {
    toast.error(err.message || 'Error al cambiar estado del alumno')
  } finally {
    changingAlumnoStatus.value = false
  }
}

const branchAlumnos = computed(() => {
  if (sucursalFilter.value === 'todas') return alumnos.value
  return alumnos.value.filter(
    (alumno) => String(alumno.sucursal) === String(sucursalFilter.value),
  )
})

const visibleAlumnos = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase('es')
  return branchAlumnos.value.filter((alumno) => {
    if (onlyActive.value && alumno.estado !== 'activo') return false
    if (!query) return true
    const searchable = [
      alumno.legajo,
      alumno.nombre,
      alumno.apellido,
      alumno.dni,
      alumno.email,
      alumno.sucursal_nombre,
    ]
      .filter(Boolean)
      .join(' ')
      .toLocaleLowerCase('es')
    return searchable.includes(query)
  })
})

const hasActiveFilters = computed(() => Boolean(
  searchQuery.value.trim()
  || sucursalFilter.value !== 'todas'
  || onlyActive.value,
))

const activeCount = computed(
  () => branchAlumnos.value.filter((alumno) => alumno.estado === 'activo').length,
)

const inactiveCount = computed(
  () => branchAlumnos.value.filter((alumno) => alumno.estado !== 'activo').length,
)

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
    value: branchAlumnos.value.length,
    detail: selectedBranchName.value,
    tone: 'primary',
    icon: UserGroupIcon,
  },
  {
    label: 'Alumnos activos',
    value: activeCount.value,
    detail: 'con matrícula vigente',
    tone: 'success',
    icon: CheckCircleIcon,
  },
  {
    label: 'Inactivos',
    value: inactiveCount.value,
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
