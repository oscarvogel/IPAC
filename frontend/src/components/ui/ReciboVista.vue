<template>
  <section class="receipt-view" aria-label="Recibo de pago">
    <h3>Recibo N.º {{ recibo.numero }}</h3>
    <p v-if="recibo.pago?.estado === 'anulado'" role="status">Pago anulado</p>
    <dl><div><dt>Alumno</dt><dd>{{ recibo.pago?.alumno_nombre }}</dd></div><div><dt>Importe</dt><dd>$ {{ formatMoney(recibo.pago?.importe) }}</dd></div><div><dt>Medio</dt><dd>{{ medioLabel(recibo.pago?.medio) }}</dd></div><div><dt>Fecha</dt><dd>{{ formatDate(recibo.pago?.fecha) }}</dd></div><div><dt>Cajero</dt><dd>{{ recibo.pago?.usuario_nombre || 'No informado' }}</dd></div></dl>
    <ul>
      <li v-for="(item, i) in recibo.aplicaciones || []" :key="i">
        {{ item.concepto }} · {{ item.periodo }} · $ {{ formatMoney(item.importe) }} {{ item.activa === false ? '(anulada)' : '' }}
        <small v-if="item.desglose_completo">Programática $ {{ formatMoney(item.importe_programatico) }} · Extraprogramática $ {{ formatMoney(item.importe_extraprogramatica) }}</small>
      </li>
    </ul>
    <p v-if="!recibo.aplicaciones?.length">Pago a cuenta.</p>
    <p v-if="recibo.pago?.observacion">{{ recibo.pago.observacion }}</p>
    <button type="button" class="primary-button" @click="imprimir">Imprimir recibo</button>
    <small>Si aparece la dirección del sitio, desactivá “Encabezados y pies de página” en el diálogo de impresión.</small>
    <Teleport to="body"><ReciboPrintView ref="printView" :recibo="recibo" /></Teleport>
  </section>
</template>
<script setup>
import { ref, nextTick } from 'vue'
import { formatMoney, formatDate } from '@/lib/formatters'
import { printDocument } from '@/lib/print'
import ReciboPrintView from '@/components/ui/ReciboPrintView.vue'
defineProps({ recibo: { type: Object, required: true } })
const printView = ref(null)
function medioLabel(value) { return { efectivo:'Efectivo', transferencia:'Transferencia', mercado_pago:'Mercado Pago', tarjeta:'Tarjeta', otro:'Otro' }[value] || value || 'No informado' }
async function imprimir() { await nextTick(); printDocument('receipt', printView.value?.$el) }
defineExpose({ imprimir })
</script>
<style scoped>
.receipt-view{display:grid;gap:.9rem}.receipt-view h3,.receipt-view p{margin:0}.receipt-view dl{display:grid;gap:.75rem}.receipt-view dl>div{display:grid;grid-template-columns:7rem 1fr;gap:.6rem}.receipt-view dt,.receipt-view small{color:var(--text-secondary)}.receipt-view dd{margin:0;overflow-wrap:anywhere}.receipt-view button{min-height:44px;width:fit-content}
</style>
