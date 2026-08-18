<template>
  <section class="branches-workspace text-text-primary">
    <AppPageState
      v-if="!pageReady"
      :loading="!pageError"
      :error="pageError"
      label="las sucursales"
      @retry="loadPage"
    />
    <template v-else>
    <div class="branches-metrics-grid cash-metrics-grid">
      <article
        v-for="(stat, index) in stats"
        :key="stat.label"
        class="branches-metric-card cash-metric-card border-border bg-surface"
        :class="{ 'cash-metric-card-featured': index === 0 }"
      >
        <span class="cash-metric-icon" :class="`cash-metric-icon-${stat.tone}`">
          <component :is="stat.icon" aria-hidden="true" />
        </span>
        <span class="cash-metric-copy">
          <span>{{ stat.label }}</span>
          <strong>{{ stat.value }}</strong>
          <small>{{ stat.detail }}</small>
        </span>
      </article>
    </div>

    <section class="branches-toolbar border-border bg-surface">
      <div class="branches-toolbar-heading">
        <span class="branches-toolbar-icon">
          <BuildingOffice2Icon aria-hidden="true" />
        </span>
        <div>
          <p class="eyebrow">Estructura institucional</p>
          <h2>Directorio de sucursales</h2>
          <p>Administrá las sedes habilitadas para operar en el CRM.</p>
        </div>
      </div>
      <button
        type="button"
        v-if="canManageBranches"
        class="branches-primary-action bg-primary hover:bg-primary-hover"
        @click="openNewSucursalForm"
      >
        <PlusIcon aria-hidden="true" />
        <span>Nueva sucursal</span>
      </button>
    </section>

    <SucursalList
      :sucursales="sucursales"
      :carreras="carreras"
      :can-edit="canManageBranches"
      :can-deactivate="canManageBranches"
      @edit="openEditForm"
      @deactivate="requestDeactivate"
    />

    <SucursalForm
      :open="showSucursalForm"
      :sucursal="editingSucursal"
      @close="closeSucursalForm"
      @saved="onSucursalSaved"
    />

    <ConfirmDialog
      :open="Boolean(pendingDeactivateSucursal)"
      title="Desactivar sucursal"
      description="La sede dejará de estar disponible para nuevas operaciones. Sus alumnos, carreras y movimientos permanecerán registrados."
      :subject="pendingDeactivateSucursal?.nombre || ''"
      confirm-label="Desactivar sede"
      :loading="deactivatingSucursal"
      @cancel="pendingDeactivateSucursal = null"
      @confirm="confirmDeactivate"
    />
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  AcademicCapIcon,
  BuildingOffice2Icon,
  CheckCircleIcon,
  PauseCircleIcon,
  PlusIcon,
} from '@heroicons/vue/24/outline'
import { useCatalogos } from '@/composables/useCatalogos'
import { useSucursales } from '@/composables/useSucursales'
import { useToast } from '@/composables/useToast'
import { useAuth } from '@/composables/useAuth'
import SucursalForm from '@/components/sucursales/SucursalForm.vue'
import SucursalList from '@/components/sucursales/SucursalList.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import AppPageState from '@/components/ui/AppPageState.vue'

const { sucursales, error: sucursalesError, loadSucursales, updateSucursal } = useSucursales()
const { carreras, loadCatalogos } = useCatalogos()
const toast = useToast()
const auth = useAuth()
const canManageBranches = computed(() => auth.can('manage-branches'))

const showSucursalForm = ref(false)
const editingSucursal = ref(null)
const pendingDeactivateSucursal = ref(null)
const deactivatingSucursal = ref(false)
const pageReady = ref(false)
const pageError = ref('')

onMounted(loadPage)

async function loadPage() {
  pageReady.value = false
  pageError.value = ''
  try {
    await Promise.all([loadSucursales(true), loadCatalogos()])
    if (sucursalesError.value) throw new Error(sucursalesError.value)
    pageReady.value = true
  } catch (err) {
    pageError.value = err.message || 'No se pudo cargar el directorio de sucursales.'
  }
}

const totalActivas = computed(() => sucursales.value.filter((s) => s.activa).length)

const stats = computed(() => [
  {
    label: 'Total de sucursales',
    value: sucursales.value.length,
    detail: 'sedes registradas',
    tone: 'primary',
    icon: BuildingOffice2Icon,
  },
  {
    label: 'Sucursales activas',
    value: totalActivas.value,
    detail: 'disponibles para operar',
    tone: 'success',
    icon: CheckCircleIcon,
  },
  {
    label: 'Inactivas',
    value: sucursales.value.length - totalActivas.value,
    detail: 'fuera de operación',
    tone: 'warning',
    icon: PauseCircleIcon,
  },
  {
    label: 'Carreras y cursos',
    value: carreras.value.length,
    detail: 'oferta académica total',
    tone: 'info',
    icon: AcademicCapIcon,
  },
])

function openNewSucursalForm() {
  editingSucursal.value = null
  showSucursalForm.value = true
}

function openEditForm(sucursal) {
  editingSucursal.value = sucursal
  showSucursalForm.value = true
}

function closeSucursalForm() {
  showSucursalForm.value = false
  editingSucursal.value = null
}

function onSucursalSaved() {
  closeSucursalForm()
}

function requestDeactivate(sucursal) {
  pendingDeactivateSucursal.value = sucursal
}

async function confirmDeactivate() {
  if (!pendingDeactivateSucursal.value) return
  deactivatingSucursal.value = true
  try {
    await updateSucursal(pendingDeactivateSucursal.value.id, { activa: false })
    toast.success('Sucursal desactivada')
    pendingDeactivateSucursal.value = null
  } catch (err) {
    toast.error(err.message || 'No se pudo desactivar la sucursal.')
  } finally {
    deactivatingSucursal.value = false
  }
}
</script>
