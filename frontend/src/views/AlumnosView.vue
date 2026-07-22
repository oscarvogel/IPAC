<template>
  <div class="crm-screen">
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
        placeholder="Buscar alumno, DNI, legajo..."
      />
      <select v-model="sucursalFilter" class="compact-select">
        <option value="todas">Todas las sucursales</option>
        <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
          {{ sucursal.nombre }}
        </option>
      </select>
    </div>

    <div class="crm-grid">
      <AlumnoList
        :alumnos="alumnos"
        :selected-alumno="selectedAlumno"
        :search-query="searchQuery"
        :sucursal-filter="sucursalFilter"
        @select="onSelect"
      />
      <AlumnoDetail
        :alumno="selectedAlumno"
        :conceptos="conceptos"
        :pagos="pagos"
        @register-pago="showPagoForm = true"
        @edit="openEdit"
        @view-estado="showEstadoCuenta = true"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useAlumnos } from '@/composables/useAlumnos'
import { useCatalogos } from '@/composables/useCatalogos'
import { usePagos } from '@/composables/usePagos'
import { setTopbarActions } from '@/composables/useTopbarActions'
import { formatMoney } from '@/lib/formatters'
import AlumnoList from '@/components/alumnos/AlumnoList.vue'
import AlumnoDetail from '@/components/alumnos/AlumnoDetail.vue'

const { alumnos, selectedAlumno, selectedAlumnoId, setSelected, loadAlumnos } = useAlumnos()
const { sucursales, conceptos, loadCatalogos } = useCatalogos()
const { pagos, loadPagos } = usePagos()

const searchQuery = ref('')
const sucursalFilter = ref('todas')
const showPagoForm = ref(false)
const showEstadoCuenta = ref(false)

onMounted(async () => {
  await Promise.all([loadCatalogos(), loadAlumnos(), loadPagos()])
  setTopbarActions([
    { label: 'Nuevo alumno', variant: 'primary', onClick: openNewAlumno },
  ])
})

onBeforeUnmount(() => {
  setTopbarActions([])
})

function onSelect(alumno) {
  setSelected(alumno.id)
}

function openNewAlumno() {
  // Se enchufa al modal de AlumnoForm en el commit 4.
  // Por ahora solo loguea para confirmar que el wiring anda.
  // eslint-disable-next-line no-console
  console.info('[AlumnosView] openNewAlumno pendiente del modal (commit 4)')
}

function openEdit() {
  // Idem: depende del modal del commit 4.
  // eslint-disable-next-line no-console
  console.info('[AlumnosView] openEdit pendiente del modal (commit 4)')
}

const totalPagado = computed(() =>
  pagos.value.reduce((sum, p) => sum + Number(p.importe || 0), 0),
)

const stats = computed(() => [
  { label: 'Alumnos activos', value: alumnos.value.length, detail: 'base cargada' },
  { label: 'Sucursales', value: sucursales.value.length, detail: 'Posadas y Eldorado' },
  { label: 'Pagos registrados', value: pagos.value.length, detail: 'movimientos cargados' },
  {
    label: 'Cobrado total',
    value: `$ ${formatMoney(totalPagado.value)}`,
    detail: 'suma de pagos',
  },
])
</script>

<style scoped>
.topbar-filters {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 4px;
}
</style>
