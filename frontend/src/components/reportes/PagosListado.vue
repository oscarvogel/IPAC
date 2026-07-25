<template>
  <div class="panel table-card">
    <div class="panel-head">
      <div>
        <h2>Pagos en el periodo</h2>
        <p>{{ pagos.length }} pagos visibles</p>
      </div>
    </div>
    <table>
      <thead>
        <tr>
          <th>Recibo</th>
          <th>Fecha</th>
          <th>Alumno</th>
          <th>Concepto</th>
          <th>Sucursal</th>
          <th>Medio</th>
          <th>Importe</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="pago in pagos" :key="pago.id">
          <td>{{ pago.numero_recibo || '—' }}</td>
          <td>{{ formatDate(pago.fecha) }}</td>
          <td>{{ pago.alumno_nombre || '—' }}</td>
          <td>{{ pago.concepto_nombre || 'Pago a cuenta' }}</td>
          <td>{{ pago.sucursal_nombre || '—' }}</td>
          <td><span class="table-badge">{{ pago.medio }}</span></td>
          <td>$ {{ formatMoney(pago.importe, { fractionDigits: 2 }) }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="!pagos.length" class="empty-state flat">
      No hay pagos para el filtro actual.
    </p>
  </div>
</template>

<script setup>
import { formatDate, formatMoney } from '@/lib/formatters'

defineProps({
  pagos: { type: Array, required: true },
})
</script>
