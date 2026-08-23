<template>
  <section class="concepts-workspace text-text-primary">
    <AppPageState
      v-if="!pageReady"
      :loading="!pageError"
      :error="pageError"
      label="los conceptos"
      @retry="loadPage"
    />
    <template v-else>
    <div class="concepts-metrics-grid">
      <article
        v-for="stat in stats"
        :key="stat.label"
        class="concepts-metric-card border-border bg-surface"
      >
        <span class="concepts-metric-icon" :class="`concepts-metric-icon-${stat.tone}`">
          <component :is="stat.icon" aria-hidden="true" />
        </span>
        <span class="concepts-metric-copy">
          <span>{{ stat.label }}</span>
          <strong>{{ stat.value }}</strong>
          <small>{{ stat.detail }}</small>
        </span>
      </article>
    </div>

    <section class="concepts-toolbar border-border bg-surface" aria-label="Filtros de conceptos">
      <div class="concepts-toolbar-heading">
        <span class="concepts-toolbar-icon">
          <TagIcon aria-hidden="true" />
        </span>
        <div>
          <p class="eyebrow">Gestión de aranceles</p>
          <h2>Catálogo de conceptos</h2>
          <p>Administrá matrículas, cuotas, materiales y otros cargos.</p>
        </div>
      </div>

      <div class="concepts-filters">
        <label class="concepts-search-field">
          <MagnifyingGlassIcon aria-hidden="true" />
          <span class="sr-only">Buscar concepto</span>
          <input v-model="searchQuery" type="search" placeholder="Buscar concepto o tipo" />
        </label>

        <label class="concepts-branch-field">
          <BuildingStorefrontIcon aria-hidden="true" />
          <span class="sr-only">Filtrar por sucursal</span>
          <select v-model="sucursalFilter">
            <option value="todas">Todas las sucursales</option>
            <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
              {{ sucursal.nombre }}
            </option>
          </select>
          <ChevronDownIcon class="concepts-select-chevron" aria-hidden="true" />
        </label>

        <label class="concepts-active-filter" :class="{ active: onlyActive }">
          <input v-model="onlyActive" class="sr-only" type="checkbox" />
          <CheckIcon aria-hidden="true" />
          <span>Solo activos</span>
        </label>

        <button
          type="button"
          v-if="canManageConcepts"
          class="concepts-primary-action bg-primary hover:bg-primary-hover"
          @click="openNewConceptoForm"
        >
          <PlusIcon aria-hidden="true" />
          <span>Nuevo concepto</span>
        </button>
      </div>
    </section>

    <ConceptoList
      :conceptos="filteredConceptos"
      :filtered="hasActiveFilters"
      :can-edit="canManageConcepts"
      :can-deactivate="canManageConcepts"
      @edit="openEditForm"
      @deactivate="requestDeactivate"
    />

    <ConceptoForm
      :open="showConceptoForm"
      :concepto="editingConcepto"
      @close="closeConceptoForm"
      @saved="onConceptoSaved"
    />

    <ConfirmDialog
      :open="Boolean(pendingDeactivateConcepto)"
      title="Desactivar concepto"
      description="El concepto dejará de estar disponible para nuevas cuotas y pagos. Los registros existentes no se modificarán."
      :subject="pendingDeactivateConcepto?.nombre || ''"
      confirm-label="Desactivar"
      :loading="deactivatingConcepto"
      @cancel="pendingDeactivateConcepto = null"
      @confirm="confirmDeactivate"
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
  CurrencyDollarIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  Squares2X2Icon,
  TagIcon,
} from '@heroicons/vue/24/outline'
import { useCatalogos } from '@/composables/useCatalogos'
import { useConceptos } from '@/composables/useConceptos'
import { useToast } from '@/composables/useToast'
import { useAuth } from '@/composables/useAuth'
import { formatMoney } from '@/lib/formatters'
import ConceptoList from '@/components/conceptos/ConceptoList.vue'
import ConceptoForm from '@/components/conceptos/ConceptoForm.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import AppPageState from '@/components/ui/AppPageState.vue'

const { sucursales, loadCatalogos } = useCatalogos()
const { conceptos, error: conceptosError, loadConceptos, deactivateConcepto } = useConceptos()
const toast = useToast()
const auth = useAuth()
const canManageConcepts = computed(() => auth.can('manage-concepts'))

const searchQuery = ref('')
const sucursalFilter = ref('todas')
const onlyActive = ref(false)

const showConceptoForm = ref(false)
const editingConcepto = ref(null)
const pendingDeactivateConcepto = ref(null)
const deactivatingConcepto = ref(false)
const pageReady = ref(false)
const pageError = ref('')

onMounted(loadPage)

async function loadPage() {
  pageReady.value = false
  pageError.value = ''
  try {
    await Promise.all([loadCatalogos(), loadConceptos()])
    if (conceptosError.value) throw new Error(conceptosError.value)
    pageReady.value = true
  } catch (err) {
    pageError.value = err.message || 'No se pudo cargar el catálogo de conceptos.'
  }
}

const branchConceptos = computed(() => {
  if (sucursalFilter.value === 'todas') return conceptos.value
  return conceptos.value.filter(
    (concepto) => String(concepto.sucursal) === String(sucursalFilter.value),
  )
})

const filteredConceptos = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return branchConceptos.value.filter((concepto) => {
    const matchesActive = !onlyActive.value || concepto.activo
    const text = [
      concepto.nombre,
      concepto.tipo,
      concepto.sucursal_nombre,
      concepto.carrera_nombre,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    const matchesQuery = !query || text.includes(query)
    return matchesActive && matchesQuery
  })
})

const hasActiveFilters = computed(() => Boolean(
  searchQuery.value.trim()
  || sucursalFilter.value !== 'todas'
  || onlyActive.value,
))

const totalActivos = computed(() => branchConceptos.value.filter((c) => c.activo).length)

const promedioImporte = computed(() => {
  const activos = branchConceptos.value.filter((c) => c.activo)
  if (!activos.length) return 0
  const suma = activos.reduce((acc, c) => acc + Number(c.importe || 0), 0)
  return suma / activos.length
})

const tiposCount = computed(
  () => new Set(branchConceptos.value.map((c) => c.tipo).filter(Boolean)).size,
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
    label: 'Total de conceptos',
    value: branchConceptos.value.length,
    detail: selectedBranchName.value,
    tone: 'primary',
    icon: TagIcon,
  },
  {
    label: 'Conceptos activos',
    value: totalActivos.value,
    detail: `${branchConceptos.value.length - totalActivos.value} inactivos`,
    tone: 'success',
    icon: CheckCircleIcon,
  },
  {
    label: 'Importe promedio',
    value: `$ ${formatMoney(promedioImporte.value, { fractionDigits: 2 })}`,
    detail: 'sobre conceptos activos',
    tone: 'info',
    icon: CurrencyDollarIcon,
  },
  {
    label: 'Tipos configurados',
    value: tiposCount.value,
    detail: 'categorías de aranceles',
    tone: 'warning',
    icon: Squares2X2Icon,
  },
])

function openNewConceptoForm() {
  editingConcepto.value = null
  showConceptoForm.value = true
}

function openEditForm(concepto) {
  editingConcepto.value = concepto
  showConceptoForm.value = true
}

function closeConceptoForm() {
  showConceptoForm.value = false
  editingConcepto.value = null
}

function onConceptoSaved() {
  closeConceptoForm()
}

function requestDeactivate(concepto) {
  pendingDeactivateConcepto.value = concepto
}

async function confirmDeactivate() {
  if (!pendingDeactivateConcepto.value) return
  deactivatingConcepto.value = true
  try {
    await deactivateConcepto(pendingDeactivateConcepto.value.id)
    toast.success('Concepto desactivado')
    pendingDeactivateConcepto.value = null
  } catch (err) {
    toast.error(err.message || 'No se pudo desactivar el concepto.')
  } finally {
    deactivatingConcepto.value = false
  }
}
</script>

<style scoped>
</style>
