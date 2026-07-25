<template>
  <section class="concepts-screen">
    <div class="stats-grid">
      <article v-for="stat in stats" :key="stat.label" class="stat-card">
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
        <small>{{ stat.detail }}</small>
      </article>
    </div>

    <div class="topbar-filters">
      <input
        v-model="searchQuery"
        class="global-search"
        placeholder="Buscar concepto..."
      />
      <select v-model="sucursalFilter" class="compact-select">
        <option value="todas">Todas las sucursales</option>
        <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
          {{ sucursal.nombre }}
        </option>
      </select>
      <label class="checkbox-inline">
        <input v-model="onlyActive" type="checkbox" />
        Solo activos
      </label>
    </div>

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
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useCatalogos } from '@/composables/useCatalogos'
import { useConceptos } from '@/composables/useConceptos'
import { setTopbarActions } from '@/composables/useTopbarActions'
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
  setTopbarActions([
    { label: 'Nuevo concepto', variant: 'primary', onClick: openNewConceptoForm },
  ])
})

onBeforeUnmount(() => {
  setTopbarActions([])
})

const filteredConceptos = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return conceptos.value.filter((concepto) => {
    const matchesSucursal =
      sucursalFilter.value === 'todas' ||
      String(concepto.sucursal) === String(sucursalFilter.value)
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
    return matchesSucursal && matchesActive && matchesQuery
  })
})

const totalActivos = computed(() => conceptos.value.filter((c) => c.activo).length)

const promedioImporte = computed(() => {
  const activos = conceptos.value.filter((c) => c.activo)
  if (!activos.length) return 0
  const suma = activos.reduce((acc, c) => acc + Number(c.importe || 0), 0)
  return suma / activos.length
})

const tiposCount = computed(
  () => new Set(conceptos.value.map((c) => c.tipo)).size,
)

const stats = computed(() => [
  {
    label: 'Conceptos activos',
    value: totalActivos.value,
    detail: `de un total de ${conceptos.value.length}`,
  },
  { label: 'Sucursales', value: sucursales.value.length, detail: 'Posadas y Eldorado' },
  {
    label: 'Importe promedio',
    value: `$ ${formatMoney(promedioImporte.value, { fractionDigits: 2 })}`,
    detail: 'sobre conceptos activos',
  },
  { label: 'Tipos', value: tiposCount.value, detail: 'matricula, cuota, material, otro' },
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
.topbar-filters {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.checkbox-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  color: #4a4a55;
}
</style>
