<template>
  <section class="cash-movements-card border-border bg-surface">
    <header class="cash-movements-head">
      <div class="cash-movements-title"><span class="cash-movements-icon"><ArrowsRightLeftIcon aria-hidden="true" /></span><div><p class="eyebrow">Actividad de hoy</p><h2>Movimientos de caja</h2><p>Ingresos, egresos, retiros, pagos y reversiones.</p></div></div>
      <span class="cash-movements-count">{{ filteredMovements.length }} de {{ movimientos.length }} movimientos</span>
    </header>
    <div class="cash-movement-filters">
      <div class="cash-type-filters" aria-label="Filtrar por tipo"><button v-for="item in typeOptions" :key="item.value" type="button" :class="{ active: typeFilter === item.value }" @click="typeFilter = item.value">{{ item.label }}</button></div>
      <label><span class="sr-only">Buscar movimiento</span><input v-model.trim="search" type="search" placeholder="Descripción o recibo" /></label>
      <label><span class="sr-only">Filtrar por medio</span><select v-model="mediumFilter"><option value="">Todos los medios</option><option v-for="item in mediumOptions" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
      <label><span class="sr-only">Ordenar movimientos</span><select v-model="ordering"><option value="recent">Más recientes</option><option value="oldest">Más antiguos</option><option value="amount">Mayor importe</option></select></label>
    </div>
    <div class="cash-movements-table-wrap">
      <table class="cash-movements-table">
        <thead><tr><th>Tipo</th><th>Medio</th><th>Descripción</th><th>Hora / cajero</th><th>Importe</th></tr></thead>
        <tbody><tr v-for="movimiento in filteredMovements" :key="movimiento.id">
          <td><span :class="['cash-movement-type', movementTone(movimiento.tipo)]"><component :is="movementIcon(movimiento.tipo)" aria-hidden="true" />{{ movimiento.tipo_label || movementLabel(movimiento.tipo) }}</span></td>
          <td><span class="cash-payment-method"><component :is="paymentIcon(movimiento.medio)" aria-hidden="true" />{{ paymentLabel(movimiento.medio) }}</span></td>
          <td class="cash-movement-description">{{ movimiento.descripcion || 'Sin descripción' }}<small v-if="movimiento.pago_numero_recibo" class="cash-movement-receipt">{{ movimiento.pago_numero_recibo }}</small></td>
          <td><strong>{{ formatTime(movimiento.creado) }}</strong><small class="cash-movement-user">{{ movimiento.usuario_nombre || 'Sin usuario' }}</small></td>
          <td :class="['cash-movement-amount', { negative: isNegative(movimiento.tipo) }]">{{ isNegative(movimiento.tipo) ? '−' : '+' }} $ {{ formatMoney(movimiento.importe, { fractionDigits: 2 }) }}</td>
        </tr></tbody>
      </table>
      <div v-if="filteredMovements.length" class="mobile-record-list cash-mobile-list" role="list">
        <article v-for="movimiento in filteredMovements" :key="`mobile-${movimiento.id}`" class="mobile-record-card cash-mobile-card" role="listitem">
          <header class="mobile-record-head"><span :class="['mobile-record-icon', movementTone(movimiento.tipo)]"><component :is="movementIcon(movimiento.tipo)" aria-hidden="true" /></span><span class="mobile-record-title"><strong>{{ movimiento.tipo_label || movementLabel(movimiento.tipo) }}</strong><small>{{ formatTime(movimiento.creado) }} · {{ paymentLabel(movimiento.medio) }}</small></span><strong :class="['mobile-record-amount', { negative: isNegative(movimiento.tipo) }]">{{ isNegative(movimiento.tipo) ? '−' : '+' }} $ {{ formatMoney(movimiento.importe, { fractionDigits: 2 }) }}</strong></header>
          <p class="mobile-record-description">{{ movimiento.descripcion || 'Sin descripción' }}</p>
          <footer class="mobile-record-footer"><span class="cash-payment-method"><component :is="paymentIcon(movimiento.medio)" aria-hidden="true" />{{ paymentLabel(movimiento.medio) }}</span><small>{{ movimiento.usuario_nombre || 'Sin usuario' }}</small></footer>
        </article>
      </div>
      <div v-if="!filteredMovements.length" class="cash-movements-empty"><span><ReceiptPercentIcon aria-hidden="true" /></span><strong>{{ movimientos.length ? 'No hay movimientos para estos filtros' : 'La caja todavía no tiene movimientos' }}</strong><p>{{ movimientos.length ? 'Probá cambiando el tipo, medio o búsqueda.' : 'Los movimientos de la jornada aparecerán en esta lista.' }}</p></div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ArrowDownCircleIcon, ArrowUpCircleIcon, ArrowsRightLeftIcon, BanknotesIcon, BuildingLibraryIcon, CreditCardIcon, QuestionMarkCircleIcon, ReceiptPercentIcon } from '@heroicons/vue/24/outline'
import { formatMoney } from '@/lib/formatters'

const props = defineProps({ movimientos: { type: Array, required: true } })
const typeFilter = ref(''); const mediumFilter = ref(''); const search = ref(''); const ordering = ref('recent')
const typeOptions = [{ value: '', label: 'Todos' }, { value: 'pago', label: 'Pagos' }, { value: 'ingreso', label: 'Ingresos' }, { value: 'egreso', label: 'Egresos' }, { value: 'retiro', label: 'Retiros' }, { value: 'reverso', label: 'Reversiones' }]
const mediumOptions = [{ value: 'efectivo', label: 'Efectivo' }, { value: 'transferencia', label: 'Transferencia' }, { value: 'mercado_pago', label: 'Mercado Pago' }, { value: 'tarjeta', label: 'Tarjeta' }, { value: 'otro', label: 'Otros' }]
const negativeTypes = new Set(['egreso', 'retiro', 'pase', 'reverso'])
const filteredMovements = computed(() => {
  const term = search.value.toLocaleLowerCase('es')
  const rows = props.movimientos.filter((item) => (!typeFilter.value || item.tipo === typeFilter.value) && (!mediumFilter.value || item.medio === mediumFilter.value) && (!term || `${item.descripcion || ''} ${item.pago_numero_recibo || ''} ${item.pago || ''}`.toLocaleLowerCase('es').includes(term)))
  return rows.sort((a, b) => ordering.value === 'amount' ? Number(b.importe) - Number(a.importe) : ordering.value === 'oldest' ? new Date(a.creado) - new Date(b.creado) : new Date(b.creado) - new Date(a.creado))
})
function isNegative(type) { return negativeTypes.has(type) }
function movementTone(type) { if (type === 'ingreso' || type === 'pago') return 'positive'; if (type === 'retiro') return 'warning'; if (negativeTypes.has(type)) return 'negative'; return 'neutral' }
function movementIcon(type) { return type === 'ingreso' || type === 'pago' ? ArrowDownCircleIcon : negativeTypes.has(type) ? ArrowUpCircleIcon : ArrowsRightLeftIcon }
function movementLabel(type) { return { ingreso: 'Ingreso', egreso: 'Egreso', retiro: 'Retiro', pase: 'Pase', pago: 'Pago', reverso: 'Reverso' }[type] || type || 'Movimiento' }
function paymentIcon(method) { if (method === 'transferencia') return BuildingLibraryIcon; if (method === 'mercado_pago' || method === 'tarjeta') return CreditCardIcon; if (method === 'efectivo') return BanknotesIcon; return QuestionMarkCircleIcon }
function paymentLabel(method) { return { efectivo: 'Efectivo', transferencia: 'Transferencia', mercado_pago: 'Mercado Pago', tarjeta: 'Tarjeta', otro: 'Otro' }[method] || method || 'Sin medio' }
function formatTime(value) { return value ? new Intl.DateTimeFormat('es-AR', { hour: '2-digit', minute: '2-digit' }).format(new Date(value)) : '—' }
</script>

<style scoped>
.cash-movement-filters{display:grid;grid-template-columns:1fr minmax(150px,220px) 165px 145px;gap:.55rem;padding:.75rem 1rem;border-top:1px solid var(--border);border-bottom:1px solid var(--border)}.cash-type-filters{display:flex;gap:.3rem;overflow-x:auto}.cash-type-filters button{min-height:2.3rem;border:1px solid var(--border);border-radius:999px;padding:0 .7rem;background:var(--surface);color:var(--text-secondary);font-size:.75rem;font-weight:800;white-space:nowrap}.cash-type-filters button.active{border-color:var(--primary);background:var(--primary-soft);color:var(--primary)}.cash-movement-filters input,.cash-movement-filters select{width:100%;min-height:2.3rem;border:1px solid var(--border);border-radius:.6rem;padding:.4rem .6rem;background:var(--surface);color:var(--text-primary)}.cash-movement-user,.cash-movement-receipt{display:block;margin-top:.15rem;color:var(--text-secondary)}
@media(max-width:1000px){.cash-movement-filters{grid-template-columns:1fr 1fr}.cash-type-filters{grid-column:1/-1}}@media(max-width:560px){.cash-movement-filters{grid-template-columns:1fr}.cash-type-filters{grid-column:auto}}
</style>
