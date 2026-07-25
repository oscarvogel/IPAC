<template>
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
            <button class="secondary-button small" type="button" @click="$emit('edit', sucursal)">
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
</template>

<script setup>
defineProps({
  sucursales: { type: Array, required: true },
})

defineEmits(['edit'])
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
