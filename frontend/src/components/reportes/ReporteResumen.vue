<template>
  <div class="reports-summary">
    <div v-if="showMetrics" class="reports-metrics-grid cash-metrics-grid">
      <article
        v-for="stat in stats"
        :key="stat.label"
        class="reports-metric-card cash-metric-card border-border bg-surface"
      >
        <span class="cash-metric-icon" :class="`cash-metric-icon-${stat.tone}`">
          <component :is="stat.icon" aria-hidden="true" />
        </span>
        <span class="cash-metric-copy">
          <span>{{ stat.label }}</span>
          <strong>{{ stat.value }}</strong>
          <small>{{ stat.detail }}</small>
        </span>
      </article>
    </div>

    <section v-if="showDistribution" class="reports-distribution-card border-border bg-surface">
      <header class="reports-distribution-head">
        <div class="reports-distribution-title">
          <span class="reports-distribution-icon">
            <ChartPieIcon aria-hidden="true" />
          </span>
          <div>
            <p class="eyebrow">Composición de ingresos</p>
            <h2>Cobrado por medio</h2>
            <p>Participación sobre el total del período seleccionado.</p>
          </div>
        </div>
        <span class="reports-distribution-total">
          Total&nbsp; $ {{ formatMoney(totalCobrado, { fractionDigits: 2 }) }}
        </span>
      </header>

      <div v-if="porMedioRows.length" class="reports-distribution-list">
        <div v-for="row in porMedioRows" :key="row.medio" class="reports-distribution-row">
          <span class="reports-method-icon">
            <component :is="paymentIcon(row.medio)" aria-hidden="true" />
          </span>
          <span class="reports-method-copy">
            <span>
              <strong>{{ paymentLabel(row.medio) }}</strong>
              <small>{{ row.porcentaje }}%</small>
            </span>
            <span class="reports-progress" aria-hidden="true">
              <span :style="{ width: `${row.porcentaje}%` }" />
            </span>
          </span>
          <strong class="reports-method-total">
            $ {{ formatMoney(row.total, { fractionDigits: 2 }) }}
          </strong>
        </div>
      </div>

      <div v-else class="reports-distribution-empty">
        <ChartPieIcon aria-hidden="true" />
        <span>Todavía no hay cobranzas para distribuir en este período.</span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  BanknotesIcon,
  BuildingLibraryIcon,
  ChartPieIcon,
  CreditCardIcon,
  ExclamationTriangleIcon,
  GiftIcon,
  LockClosedIcon,
  QuestionMarkCircleIcon,
} from '@heroicons/vue/24/outline'
import { formatMoney } from '@/lib/formatters'

const props = defineProps({
  resumen: { type: Object, default: null },
  showMetrics: { type: Boolean, default: true },
  showDistribution: { type: Boolean, default: true },
})

const totalCobrado = computed(
  () => Number(props.resumen?.cobranzas?.total || 0),
)
const cantidadPagos = computed(
  () => props.resumen?.cobranzas?.cantidad_pagos ?? 0,
)
const deudaPendiente = computed(
  () => Math.max(Number(props.resumen?.cuenta_corriente?.deuda || 0), 0),
)
const saldoAFavor = computed(
  () => Math.max(Number(props.resumen?.cuenta_corriente?.saldo_a_favor || 0), 0),
)
const cajasCerradas = computed(
  () => props.resumen?.cajas?.cerradas ?? 0,
)

const stats = computed(() => [
  {
    label: 'Total cobrado',
    value: `$ ${formatMoney(totalCobrado.value, { fractionDigits: 2 })}`,
    detail: `${cantidadPagos.value} pagos en el período`,
    tone: 'primary',
    icon: BanknotesIcon,
  },
  {
    label: 'Deuda pendiente',
    value: `$ ${formatMoney(deudaPendiente.value, { fractionDigits: 2 })}`,
    detail: 'importe total que aún deben los alumnos',
    tone: 'warning',
    icon: ExclamationTriangleIcon,
  },
  {
    label: 'Saldo a favor',
    value: `$ ${formatMoney(saldoAFavor.value, { fractionDigits: 2 })}`,
    detail: 'crédito disponible de los alumnos',
    tone: 'success',
    icon: GiftIcon,
  },
  {
    label: 'Cajas cerradas',
    value: cajasCerradas.value,
    detail: 'en el período seleccionado',
    tone: 'info',
    icon: LockClosedIcon,
  },
])

const porMedioRows = computed(() => {
  const porMedio = props.resumen?.cobranzas?.por_medio || {}
  const total = totalCobrado.value
  return Object.entries(porMedio)
    .map(([medio, totalMedio]) => ({
      medio,
      total: Number(totalMedio || 0),
      porcentaje: total > 0 ? Math.round((Number(totalMedio || 0) / total) * 100) : 0,
    }))
    .sort((a, b) => b.total - a.total)
})

function paymentIcon(method) {
  if (method === 'efectivo') return BanknotesIcon
  if (method === 'transferencia') return BuildingLibraryIcon
  if (method === 'mercado_pago') return CreditCardIcon
  if (method === 'tarjeta') return CreditCardIcon
  return QuestionMarkCircleIcon
}

function paymentLabel(method) {
  const labels = {
    efectivo: 'Efectivo',
    transferencia: 'Transferencia',
    mercado_pago: 'Mercado Pago',
    tarjeta: 'Tarjeta',
    otro: 'Otro',
  }
  return labels[method] || method || 'Sin medio'
}
</script>
