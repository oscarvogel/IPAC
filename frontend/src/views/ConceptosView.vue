<template>
  <section class="concepts-workspace text-text-primary">
    <div class="concepts-metrics-grid">
      <article
        v-for="(stat, index) in stats"
        :key="stat.label"
        class="concepts-metric-card border-border bg-surface"
        :class="{ 'concepts-metric-card-featured': index === 0 }"
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
      @edit="openEditForm"
      @deactivate="confirmDeactivate"
    />

    <ConceptoForm
      :open="showConceptoForm"
      :concepto="editingConcepto"
      @close="closeConceptoForm"
      @saved="onConceptoSaved"
    />
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
import { formatMoney } from '@/lib/formatters'
import ConceptoList from '@/components/conceptos/ConceptoList.vue'
import ConceptoForm from '@/components/conceptos/ConceptoForm.vue'

const { sucursales, loadCatalogos } = useCatalogos()
const { conceptos, loadConceptos, deactivateConcepto } = useConceptos()
const toast = useToast()

const searchQuery = ref('')
const sucursalFilter = ref('todas')
const onlyActive = ref(false)

const showConceptoForm = ref(false)
const editingConcepto = ref(null)

onMounted(async () => {
  await Promise.all([loadCatalogos(), loadConceptos()])
})

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

async function confirmDeactivate(concepto) {
  try {
    await deactivateConcepto(concepto.id)
    toast.success('Concepto desactivado')
  } catch (err) {
    toast.error(err.message || 'No se pudo desactivar el concepto.')
  }
}
</script>

<style scoped>
</style>
