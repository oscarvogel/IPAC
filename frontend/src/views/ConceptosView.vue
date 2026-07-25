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

    <div class="panel table-card">
      <div class="panel-head">
        <div>
          <h2>Conceptos cobrables</h2>
          <p>{{ filteredConceptos.length }} conceptos visibles</p>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Tipo</th>
            <th>Importe</th>
            <th>Sucursal</th>
            <th>Carrera</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="concepto in filteredConceptos" :key="concepto.id">
            <td>{{ concepto.nombre }}</td>
            <td><span class="table-badge">{{ concepto.tipo }}</span></td>
            <td>$ {{ formatMoney(concepto.importe, { fractionDigits: 2 }) }}</td>
            <td>{{ concepto.sucursal_nombre || 'Sin sucursal' }}</td>
            <td>{{ concepto.carrera_nombre || 'Aplica a todas' }}</td>
            <td>
              <span :class="concepto.activo ? 'status-pill active' : 'status-pill inactive'">
                {{ concepto.activo ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="row-actions">
              <button class="secondary-button small" type="button" @click="openEditForm(concepto)">
                Editar
              </button>
              <button
                v-if="concepto.activo"
                class="secondary-button small danger"
                type="button"
                @click="confirmDeactivate(concepto)"
              >
                Desactivar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!filteredConceptos.length" class="empty-state flat">
        No hay conceptos para el filtro actual.
      </p>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useCatalogos } from '@/composables/useCatalogos'
import { useConceptos } from '@/composables/useConceptos'
import { setTopbarActions } from '@/composables/useTopbarActions'
import { useToast } from '@/composables/useToast'
import { formatMoney } from '@/lib/formatters'

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

.row-actions {
  display: flex;
  gap: 6px;
}

.secondary-button.small {
  padding: 4px 10px;
  font-size: 0.85rem;
}

.secondary-button.danger {
  color: #b1351b;
  border-color: #e3b9b1;
}

.status-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
}

.status-pill.active {
  background: #e2f5e8;
  color: #1f6f3a;
}

.status-pill.inactive {
  background: #f3e0dc;
  color: #8a2e1c;
}
</style>
