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
            <span :class="concepto.activo ? 'status-pill active' : 'status-pill inactive'">
              {{ concepto.activo ? 'Activo' : 'Inactivo' }}
            </span>
          </td>
          <td class="row-actions">
            <button class="secondary-button small" type="button" @click="$emit('edit', concepto)">
              Editar
            </button>
            <button
              v-if="concepto.activo"
              class="secondary-button small danger"
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
