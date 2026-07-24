<template>
  <section class="cash-print-summary" aria-hidden="true">
    <header><strong>IPAC</strong><span>Resumen de caja</span></header>
    <h1>{{ sucursalLabel }}</h1>
    <p>{{ cajaHoy?.fecha }} · Usuario: {{ username }} · Estado: {{ cajaHoy?.estado }}</p>
    <div class="print-totals">
      <div><span>Total esperado</span><strong>$ {{ formatMoney(cajaTotales.total) }}</strong></div>
      <div><span>Efectivo</span><strong>$ {{ formatMoney(cajaTotales.efectivo) }}</strong></div>
      <div><span>Transferencia</span><strong>$ {{ formatMoney(cajaTotales.transferencia) }}</strong></div>
      <div v-if="cajaHoy?.estado === 'cerrada'">
        <span>Total contado</span><strong>$ {{ formatMoney(cajaHoy.total_contado) }}</strong>
      </div>
      <div v-if="cajaHoy?.estado === 'cerrada'">
        <span>Diferencia</span><strong>$ {{ formatMoney(cajaHoy.diferencia) }}</strong>
      </div>
    </div>
    <table>
      <thead>
        <tr><th>Tipo</th><th>Medio</th><th>Descripcion</th><th>Importe</th></tr>
      </thead>
      <tbody>
        <tr v-for="movimiento in movimientos" :key="`print-${movimiento.id}`">
          <td>{{ movimiento.tipo_label }}</td>
          <td>{{ movimiento.medio }}</td>
          <td>{{ movimiento.descripcion || 'Sin descripcion' }}</td>
          <td>$ {{ formatMoney(movimiento.importe) }}</td>
        </tr>
        <tr v-if="!movimientos.length"><td colspan="4">No hay movimientos registrados.</td></tr>
      </tbody>
    </table>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney } from '@/lib/formatters'

const props = defineProps({
  cajaHoy: { type: Object, default: null },
  movimientos: { type: Array, required: true },
  cajaTotales: { type: Object, required: true },
  username: { type: String, default: '' },
  fallbackSucursal: { type: String, default: '' },
})

const sucursalLabel = computed(
  () => props.cajaHoy?.sucursal_nombre || props.fallbackSucursal || '',
)
</script>
