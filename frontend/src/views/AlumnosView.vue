<template>
  <div class="crm-screen">
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
import { onMounted, ref, watch } from 'vue'
import { useAlumnos } from '@/composables/useAlumnos'
import { useCatalogos } from '@/composables/useCatalogos'
import { usePagos } from '@/composables/usePagos'
import AlumnoList from '@/components/alumnos/AlumnoList.vue'
import AlumnoDetail from '@/components/alumnos/AlumnoDetail.vue'

const { alumnos, selectedAlumno, selectedAlumnoId, setSelected, loadAlumnos } = useAlumnos()
const { conceptos, loadCatalogos } = useCatalogos()
const { pagos, loadPagos } = usePagos()

const searchQuery = ref('')
const sucursalFilter = ref('todas')
const showPagoForm = ref(false)
const showEstadoCuenta = ref(false)

onMounted(async () => {
  await Promise.all([loadCatalogos(), loadAlumnos(), loadPagos()])
})

function onSelect(alumno) {
  setSelected(alumno.id)
}

function openEdit() {
  // El modal de edicion llega en el commit 4.
  // Por ahora lo dejamos como placeholder para no romper el binding.
}

watch(
  () => [alumnos.value.length],
  () => {
    if (!selectedAlumnoId.value && alumnos.value.length) {
      setSelected(alumnos.value[0].id)
    }
  },
)
</script>
