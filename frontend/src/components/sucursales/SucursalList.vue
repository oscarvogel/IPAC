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
            <span :class="'estado-badge ' + (sucursal.activa ? 'activo' : 'inactivo')">
              {{ sucursal.activa ? 'Activa' : 'Inactiva' }}
            </span>
          </td>
          <td class="table-actions">
            <button class="secondary-button" type="button" @click="$emit('edit', sucursal)">
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
</style>
