<template>
  <section class="branches-screen">
    <div class="stats-grid">
      <article v-for="stat in stats" :key="stat.label" class="stat-card">
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
        <small>{{ stat.detail }}</small>
      </article>
    </div>

    <div class="topbar-filters">
      <button type="button" class="primary-button" @click="openNewSucursalForm">Nueva sucursal</button>
    </div>
    <SucursalList :sucursales="sucursales" @edit="openEditForm" />

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
import { useSucursales } from '@/composables/useSucursales'
import SucursalForm from '@/components/sucursales/SucursalForm.vue'
import SucursalList from '@/components/sucursales/SucursalList.vue'

const { sucursales, loadSucursales } = useSucursales()

const showSucursalForm = ref(false)
const editingSucursal = ref(null)

onMounted(async () => {
  await loadSucursales()
})

const totalActivas = computed(() => sucursales.value.filter((s) => s.activa).length)

const stats = computed(() => [
  { label: 'Sucursales totales', value: sucursales.value.length, detail: 'base cargada' },
  { label: 'Activas', value: totalActivas.value, detail: 'disponibles para operar' },
  {
    label: 'Inactivas',
    value: sucursales.value.length - totalActivas.value,
    detail: 'fuera de operacion',
  },
  { label: 'Modulo', value: 'Sucursales', detail: 'configuracion inicial' },
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
</script>
