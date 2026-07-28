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
      <label class="checkbox-inline">
        <input v-model="onlyActive" type="checkbox" />
        Solo activos
      </label>
      <button type="button" class="primary-button" @click="openNewAlumnoForm">Nuevo alumno</button>
    </div>

    <div class="crm-grid">
      <AlumnoList
        :alumnos="filteredAlumnos"
        :selected-alumno="selectedAlumno"
        :search-query="searchQuery"
        :sucursal-filter="sucursalFilter"
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
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAlumnos } from '@/composables/useAlumnos'
import { useCatalogos } from '@/composables/useCatalogos'
import { usePagos } from '@/composables/usePagos'
import { useToast } from '@/composables/useToast'
import { formatMoney } from '@/lib/formatters'
import AlumnoList from '@/components/alumnos/AlumnoList.vue'
import AlumnoDetail from '@/components/alumnos/AlumnoDetail.vue'
import AlumnoForm from '@/components/alumnos/AlumnoForm.vue'
import PagoForm from '@/components/alumnos/PagoForm.vue'
import EstadoCuentaModal from '@/components/alumnos/EstadoCuentaModal.vue'
import GenerarCuotaModal from '@/components/alumnos/GenerarCuotaModal.vue'

const { alumnos, selectedAlumno, setSelected, loadAlumnos, deactivateAlumno, reactivateAlumno } = useAlumnos()
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

onMounted(async () => {
  await Promise.all([loadCatalogos(), loadAlumnos(), loadPagos()])
})

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

async function handleToggleEstado(alumno) {
  try {
    if (alumno.estado === 'inactivo') {
      await reactivateAlumno(alumno.id)
      toast.success('Alumno reactivado')
    } else {
      await deactivateAlumno(alumno.id)
      toast.success('Alumno dado de baja')
    }
  } catch (err) {
    toast.error(err.message || 'Error al cambiar estado del alumno')
  }
}

const filteredAlumnos = computed(() => {
  if (!onlyActive.value) return alumnos.value
  return alumnos.value.filter((a) => a.estado === 'activo')
})

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
</style>
