<template>
  <section class="branches-workspace text-text-primary">
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
      @edit="openEditForm"
      @deactivate="confirmDeactivate"
    />

    <SucursalForm
      :open="showSucursalForm"
      :sucursal="editingSucursal"
      @close="closeSucursalForm"
      @saved="onSucursalSaved"
    />
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
import SucursalForm from '@/components/sucursales/SucursalForm.vue'
import SucursalList from '@/components/sucursales/SucursalList.vue'

const { sucursales, loadSucursales, updateSucursal } = useSucursales()
const { carreras, loadCatalogos } = useCatalogos()
const toast = useToast()

const showSucursalForm = ref(false)
const editingSucursal = ref(null)

onMounted(async () => {
  await Promise.all([loadSucursales(), loadCatalogos()])
})

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

async function confirmDeactivate(sucursal) {
  try {
    await updateSucursal(sucursal.id, { activa: false })
    toast.success('Sucursal desactivada')
  } catch (err) {
    toast.error(err.message || 'No se pudo desactivar la sucursal.')
  }
}
</script>
