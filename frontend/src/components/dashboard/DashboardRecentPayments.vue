<template>
  <div class="payments-table-wrap">
    <table class="payments-table">
      <thead>
        <tr>
          <th>Recibo</th>
          <th>Fecha</th>
          <th>Alumno</th>
          <th>Medio</th>
          <th>Importe</th>
          <th><span class="sr-only">Acciones</span></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="pago in pagos" :key="pago.id">
          <td>{{ pago.numero_recibo || '—' }}</td>
          <td>{{ formatDate(pago.fecha) }}</td>
          <td>{{ pago.alumno_nombre || '—' }}</td>
          <td>
            <span class="payment-method">
              <component :is="paymentIcon(pago.medio)" aria-hidden="true" />
              {{ paymentLabel(pago.medio) }}
            </span>
          </td>
          <td class="payment-amount">
            $ {{ formatMoney(pago.importe, { fractionDigits: 2 }) }}
          </td>
          <td class="payment-actions">
            <button type="button" aria-label="Más opciones">
              <EllipsisVerticalIcon aria-hidden="true" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <div v-if="pagos.length" class="dashboard-payments-mobile" role="list" aria-label="Últimos pagos">
    <article v-for="pago in pagos" :key="`mobile-${pago.id}`" class="dashboard-payment-mobile-card" role="listitem">
      <header>
        <div>
          <strong>{{ pago.numero_recibo || 'Sin recibo' }}</strong>
          <span>{{ formatDate(pago.fecha) }}</span>
        </div>
        <strong class="dashboard-payment-mobile-amount">
          $ {{ formatMoney(pago.importe, { fractionDigits: 2 }) }}
        </strong>
      </header>
      <p>{{ pago.alumno_nombre || 'Alumno sin identificar' }}</p>
      <span class="payment-method">
        <component :is="paymentIcon(pago.medio)" aria-hidden="true" />
        {{ paymentLabel(pago.medio) }}
      </span>
    </article>
  </div>

  <div v-if="!pagos.length" class="dashboard-empty-state">
    <span><DocumentMagnifyingGlassIcon aria-hidden="true" /></span>
    <strong>Todavía no hay pagos este mes</strong>
    <p>Las próximas cobranzas aparecerán acá automáticamente.</p>
  </div>
</template>

<script setup>
import {
  BanknotesIcon,
  CreditCardIcon,
  DocumentMagnifyingGlassIcon,
  EllipsisVerticalIcon,
} from '@heroicons/vue/24/outline'
import { formatDate, formatMoney } from '@/lib/formatters'

defineProps({
  pagos: { type: Array, default: () => [] },
})

function paymentLabel(medio) {
  const labels = {
    efectivo: 'efectivo',
    transferencia: 'transferencia',
    mercado_pago: 'Mercado Pago',
    tarjeta: 'tarjeta',
    otro: 'otro',
  }
  return labels[medio] || medio || 'otro'
}

function paymentIcon(medio) {
  return medio === 'tarjeta' ? CreditCardIcon : BanknotesIcon
}
</script>
