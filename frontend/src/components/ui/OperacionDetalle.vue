<template>
  <Teleport to="body">
    <div v-if="operacion" class="operation-backdrop" @click.self="$emit('close')">
      <section ref="panel" v-focus-trap="{ close: () => $emit('close'), returnFocus }" class="operation-panel" role="dialog" aria-modal="true" aria-labelledby="operation-title">
        <header><h2 id="operation-title">{{ showingReceipt ? 'Recibo de pago' : 'Detalle de operación' }}</h2><button type="button" class="secondary-button" @click="$emit('close')">Cerrar detalle</button></header>
        <div class="operation-body">
          <template v-if="!showingReceipt">
            <p class="operation-amount">$ {{ formatMoney(operacion.importe) }}</p>
            <dl><div v-for="field in fields" :key="field.label"><dt>{{ field.label }}</dt><dd>{{ field.value || 'No informado' }}</dd></div></dl>
            <button v-if="paymentId" class="primary-button" type="button" :disabled="loading" @click="openReceipt">{{ loading ? 'Cargando recibo…' : 'Ver recibo' }}</button>
          </template>
          <template v-else><button type="button" class="secondary-button" @click="showingReceipt = false">Volver al detalle</button><ReciboVista v-if="receipt" :recibo="receipt" /></template>
          <p v-if="error" role="alert">{{ error }} <button type="button" class="secondary-button" @click="openReceipt">Reintentar recibo</button></p>
        </div>
      </section>
    </div>
  </Teleport>
</template>
<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { usePagos } from '@/composables/usePagos'
import { formatMoney, formatDate, formatDateTime } from '@/lib/formatters'
import { vFocusTrap } from '@/directives/accessibility'
import ReciboVista from '@/components/ui/ReciboVista.vue'
const props = defineProps({ operacion: { type: Object, default: null }, tipo: { type: String, default: 'movimiento' }, returnFocus: { type: Object, default: null } })
defineEmits(['close'])
const { getRecibo } = usePagos()
const receipt = ref(null), showingReceipt = ref(false), error = ref(''), loading = ref(false)
const panel = ref(null)
watch(showingReceipt, async () => { await nextTick(); panel.value?.querySelector('.operation-body button')?.focus() })
watch(() => Boolean(props.operacion), (open, previous, onCleanup) => {
  if (!open) return
  const overflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  onCleanup(() => { document.body.style.overflow = overflow })
}, { immediate: true, flush: 'sync' })
let revision = 0
const paymentId = computed(() => props.tipo === 'pago' ? props.operacion?.id : props.operacion?.pago)
const fields = computed(() => { const item = props.operacion || {}; return [
  { label: 'Tipo', value: item.tipo_label || item.tipo || 'Pago' }, { label: 'Medio', value: { efectivo:'Efectivo', transferencia:'Transferencia', mercado_pago:'Mercado Pago', tarjeta:'Tarjeta', otro:'Otro' }[item.medio] || item.medio },
  { label: 'Fecha', value: item.creado ? formatDateTime(item.creado) : formatDate(item.fecha) }, { label: 'Descripción', value: item.descripcion || item.observacion || item.concepto_nombre }, { label: 'Cajero', value: item.usuario_nombre }, { label: 'Referencia', value: item.numero_recibo || item.pago_numero_recibo || (item.movimiento_origen ? `Movimiento ${item.movimiento_origen}` : '') }, { label: 'Alumno', value: item.alumno_nombre }, { label: 'Estado', value: item.estado },
] })
watch(() => props.operacion, () => { revision++; receipt.value = null; showingReceipt.value = false; error.value = ''; loading.value = false })
async function openReceipt() {
  if (loading.value || !paymentId.value) return
  const current = revision
  loading.value = true; error.value = ''
  try { const data = await getRecibo(paymentId.value); if (current === revision) { receipt.value = data; showingReceipt.value = true } }
  catch (err) { if (current === revision) error.value = err.message }
  finally { if (current === revision) loading.value = false }
}
</script>
<style scoped>
.operation-backdrop{position:fixed;inset:0;z-index:1000;background:rgb(0 0 0 / .4);display:flex;justify-content:flex-end}.operation-panel{width:min(520px,100%);height:100dvh;background:var(--surface);color:var(--text-primary);display:flex;flex-direction:column;box-shadow:var(--shadow-lg)}.operation-panel header{padding:1rem;display:flex;align-items:center;gap:1rem;justify-content:space-between;border-bottom:1px solid var(--border)}.operation-panel h2{font-size:1.15rem;margin:0}.operation-body{padding:1.25rem;overflow:auto;display:grid;align-content:start;gap:1rem}.operation-amount{font-size:1.7rem;font-weight:800;margin:0}.operation-body dl{display:grid;gap:1rem}.operation-body dl>div{display:grid;grid-template-columns:7rem 1fr;gap:.65rem}.operation-body dt{color:var(--text-secondary)}.operation-body dd{margin:0;overflow-wrap:anywhere}.operation-panel button{min-height:44px;white-space:normal}.operation-panel :focus-visible{outline:3px solid var(--primary);outline-offset:2px}.operation-body [role=alert]{color:var(--danger)}@media(max-width:560px){.operation-panel{width:100%}}
</style>
