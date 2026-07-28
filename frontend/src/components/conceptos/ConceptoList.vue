<template>
  <div class="panel table-card">
    <div class="panel-head">
      <div>
        <h2>Conceptos cobrables</h2>
        <p>{{ conceptos.length }} conceptos visibles</p>
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
        <tr v-for="concepto in conceptos" :key="concepto.id">
          <td>{{ concepto.nombre }}</td>
          <td><span class="table-badge">{{ concepto.tipo }}</span></td>
          <td>$ {{ formatMoney(concepto.importe, { fractionDigits: 2 }) }}</td>
          <td>{{ concepto.sucursal_nombre || 'Sin sucursal' }}</td>
          <td>{{ concepto.carrera_nombre || 'Aplica a todas' }}</td>
          <td>
            <span :class="'estado-badge ' + (concepto.activo ? 'activo' : 'inactivo')">
              {{ concepto.activo ? 'Activo' : 'Inactivo' }}
            </span>
          </td>
          <td class="table-actions">
            <button class="secondary-button" type="button" @click="$emit('edit', concepto)">
              Editar
            </button>
            <button
              v-if="concepto.activo"
              class="danger-button"
              type="button"
              @click="$emit('deactivate', concepto)"
            >
              Desactivar
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!conceptos.length" class="empty-state flat">
      No hay conceptos para el filtro actual.
    </p>
  </div>
</template>

<script setup>
import { formatMoney } from '@/lib/formatters'

defineProps({
  conceptos: { type: Array, required: true },
})

defineEmits(['edit', 'deactivate'])
</script>

<style scoped>
</style>
