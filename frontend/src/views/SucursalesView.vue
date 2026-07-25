<template>
  <section class="branches-screen">
    <div class="stats-grid">
      <article v-for="stat in stats" :key="stat.label" class="stat-card">
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
        <small>{{ stat.detail }}</small>
      </article>
    </div>

    <div class="panel table-card">
      <div class="panel-head">
        <div>
          <h2>Sucursales</h2>
          <p>{{ sucursales.length }} sucursales visibles</p>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Codigo</th>
            <th>Nombre</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sucursal in sucursales" :key="sucursal.id">
            <td>{{ sucursal.codigo }}</td>
            <td>{{ sucursal.nombre }}</td>
            <td>
              <span :class="sucursal.activa ? 'status-pill active' : 'status-pill inactive'">
                {{ sucursal.activa ? 'Activa' : 'Inactiva' }}
              </span>
            </td>
            <td class="row-actions">
              <button class="secondary-button small" type="button" @click="openEditForm(sucursal)">
                Editar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!sucursales.length" class="empty-state flat">
        No hay sucursales cargadas.
      </p>
    </div>

    <SucursalForm
      :open="showSucursalForm"
      :sucursal="editingSucursal"
      @close="closeSucursalForm"
      @saved="onSucursalSaved"
    />
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { setTopbarActions } from '@/composables/useTopbarActions'
import { useSucursales } from '@/composables/useSucursales'
import SucursalForm from '@/components/sucursales/SucursalForm.vue'

const { sucursales, loadSucursales } = useSucursales()

const showSucursalForm = ref(false)
const editingSucursal = ref(null)

onMounted(async () => {
  await loadSucursales()
  setTopbarActions([
    { label: 'Nueva sucursal', variant: 'primary', onClick: openNewSucursalForm },
  ])
})

onBeforeUnmount(() => {
  setTopbarActions([])
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

<style scoped>
.row-actions {
  display: flex;
  gap: 6px;
}

.secondary-button.small {
  padding: 4px 10px;
  font-size: 0.85rem;
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
