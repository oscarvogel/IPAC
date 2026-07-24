<template>
  <div class="panel table-card">
    <div class="panel-head">
      <div>
        <h2>Movimientos de caja</h2>
        <p>Pagos, ingresos, egresos, retiros y pases</p>
      </div>
    </div>
    <table>
      <thead>
        <tr><th>Tipo</th><th>Medio</th><th>Descripcion</th><th>Importe</th></tr>
      </thead>
      <tbody>
        <tr v-for="movimiento in movimientos" :key="movimiento.id">
          <td><span class="table-badge">{{ movimiento.tipo_label }}</span></td>
          <td>{{ movimiento.medio }}</td>
          <td>{{ movimiento.descripcion || 'Sin descripcion' }}</td>
          <td>$ {{ formatMoney(movimiento.importe) }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="!movimientos.length" class="empty-state flat">
      Todavia no hay movimientos en esta caja.
    </p>
  </div>
</template>

<script setup>
import { formatMoney } from '@/lib/formatters'

defineProps({
  movimientos: { type: Array, required: true },
})
</script>
