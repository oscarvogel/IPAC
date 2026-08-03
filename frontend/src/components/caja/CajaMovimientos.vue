<template>
  <section class="cash-movements-card border-border bg-surface">
    <header class="cash-movements-head">
      <div class="cash-movements-title">
        <span class="cash-movements-icon">
          <ArrowsRightLeftIcon aria-hidden="true" />
        </span>
        <div>
          <p class="eyebrow">Actividad de hoy</p>
          <h2>Movimientos de caja</h2>
          <p>Ingresos, egresos, retiros y pagos registrados.</p>
        </div>
      </div>
      <span class="cash-movements-count">
        {{ movimientos.length }} {{ movimientos.length === 1 ? 'movimiento' : 'movimientos' }}
      </span>
    </header>

    <div class="cash-movements-table-wrap">
      <table class="cash-movements-table">
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Medio</th>
            <th>Descripción</th>
            <th>Importe</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="movimiento in movimientos" :key="movimiento.id">
            <td>
              <span :class="['cash-movement-type', movementTone(movimiento.tipo)]">
                <component :is="movementIcon(movimiento.tipo)" aria-hidden="true" />
                {{ movimiento.tipo_label || movementLabel(movimiento.tipo) }}
              </span>
            </td>
            <td>
              <span class="cash-payment-method">
                <component :is="paymentIcon(movimiento.medio)" aria-hidden="true" />
                {{ paymentLabel(movimiento.medio) }}
              </span>
            </td>
            <td class="cash-movement-description">
              {{ movimiento.descripcion || 'Sin descripción' }}
            </td>
            <td :class="['cash-movement-amount', { negative: isNegative(movimiento.tipo) }]">
              {{ isNegative(movimiento.tipo) ? '−' : '+' }}
              $ {{ formatMoney(movimiento.importe, { fractionDigits: 2 }) }}
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="movimientos.length" class="mobile-record-list cash-mobile-list" role="list">
        <article
          v-for="movimiento in movimientos"
          :key="`mobile-${movimiento.id}`"
          class="mobile-record-card cash-mobile-card"
          role="listitem"
        >
          <header class="mobile-record-head">
            <span :class="['mobile-record-icon', movementTone(movimiento.tipo)]">
              <component :is="movementIcon(movimiento.tipo)" aria-hidden="true" />
            </span>
            <span class="mobile-record-title">
              <strong>{{ movimiento.tipo_label || movementLabel(movimiento.tipo) }}</strong>
              <small>{{ paymentLabel(movimiento.medio) }}</small>
            </span>
            <strong :class="['mobile-record-amount', { negative: isNegative(movimiento.tipo) }]">
              {{ isNegative(movimiento.tipo) ? '−' : '+' }}
              $ {{ formatMoney(movimiento.importe, { fractionDigits: 2 }) }}
            </strong>
          </header>

          <p class="mobile-record-description">
            {{ movimiento.descripcion || 'Sin descripción' }}
          </p>

          <footer class="mobile-record-footer">
            <span class="cash-payment-method">
              <component :is="paymentIcon(movimiento.medio)" aria-hidden="true" />
              {{ paymentLabel(movimiento.medio) }}
            </span>
          </footer>
        </article>
      </div>

      <div v-if="!movimientos.length" class="cash-movements-empty">
        <span><ReceiptPercentIcon aria-hidden="true" /></span>
        <strong>La caja todavía no tiene movimientos</strong>
        <p>Los ingresos, egresos y pagos de la jornada aparecerán en esta lista.</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import {
  ArrowDownCircleIcon,
  ArrowUpCircleIcon,
  ArrowsRightLeftIcon,
  BanknotesIcon,
  BuildingLibraryIcon,
  CreditCardIcon,
  QuestionMarkCircleIcon,
  ReceiptPercentIcon,
} from '@heroicons/vue/24/outline'
import { formatMoney } from '@/lib/formatters'

defineProps({
  movimientos: { type: Array, required: true },
})

const negativeTypes = new Set(['egreso', 'retiro', 'pase'])

function isNegative(type) {
  return negativeTypes.has(type)
}

function movementTone(type) {
  if (type === 'ingreso' || type === 'pago') return 'positive'
  if (type === 'retiro') return 'warning'
  if (type === 'egreso' || type === 'pase') return 'negative'
  return 'neutral'
}

function movementIcon(type) {
  if (type === 'ingreso' || type === 'pago') return ArrowDownCircleIcon
  if (negativeTypes.has(type)) return ArrowUpCircleIcon
  return ArrowsRightLeftIcon
}

function movementLabel(type) {
  const labels = {
    ingreso: 'Ingreso',
    egreso: 'Egreso',
    retiro: 'Retiro',
    pase: 'Pase',
    pago: 'Pago',
  }
  return labels[type] || type || 'Movimiento'
}

function paymentIcon(method) {
  if (method === 'transferencia') return BuildingLibraryIcon
  if (method === 'tarjeta') return CreditCardIcon
  if (method === 'efectivo') return BanknotesIcon
  return QuestionMarkCircleIcon
}

function paymentLabel(method) {
  const labels = {
    efectivo: 'Efectivo',
    transferencia: 'Transferencia',
    tarjeta: 'Tarjeta',
    otro: 'Otro',
  }
  return labels[method] || method || 'Sin medio'
}
</script>
