<template>
  <div class="report-resumen">
    <div class="stats-grid">
      <article v-for="stat in stats" :key="stat.label" class="stat-card">
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
        <small>{{ stat.detail }}</small>
      </article>
    </div>

    <div v-if="resumen" class="panel table-card small">
      <div class="panel-head">
        <div>
          <h2>Cobrado por medio</h2>
          <p>Distribucion del periodo seleccionado</p>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Medio</th>
            <th>Total</th>
            <th>Participacion</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in porMedioRows" :key="row.medio">
            <td><span class="table-badge">{{ row.medio }}</span></td>
            <td>$ {{ formatMoney(row.total, { fractionDigits: 2 }) }}</td>
            <td>{{ row.porcentaje }}%</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney } from '@/lib/formatters'

const props = defineProps({
  resumen: { type: Object, default: null },
})

const totalCobrado = computed(
  () => Number(props.resumen?.cobranzas?.total || 0),
)
const cantidadPagos = computed(
  () => props.resumen?.cobranzas?.cantidad_pagos ?? 0,
)
const deudaNeta = computed(
  () => Number(props.resumen?.cuenta_corriente?.saldo_neto || 0),
)
const cajasCerradas = computed(
  () => props.resumen?.cajas?.cerradas ?? 0,
)

const stats = computed(() => [
  {
    label: 'Total cobrado',
    value: `$ ${formatMoney(totalCobrado.value, { fractionDigits: 2 })}`,
    detail: `${cantidadPagos.value} pagos en el periodo`,
  },
  {
    label: 'Cantidad de pagos',
    value: cantidadPagos.value,
    detail: 'filtrados por el periodo y la sucursal',
  },
  {
    label: 'Deuda neta',
    value: `$ ${formatMoney(deudaNeta.value, { fractionDigits: 2 })}`,
    detail: 'saldo pendiente menos saldo a favor',
  },
  {
    label: 'Cajas cerradas',
    value: cajasCerradas.value,
    detail: 'en el periodo seleccionado',
  },
])

const porMedioRows = computed(() => {
  const porMedio = props.resumen?.cobranzas?.por_medio || {}
  const total = totalCobrado.value
  return Object.entries(porMedio).map(([medio, totalMedio]) => ({
    medio,
    total: Number(totalMedio || 0),
    porcentaje: total > 0 ? Math.round((Number(totalMedio || 0) / total) * 100) : 0,
  }))
})
</script>

<style scoped>
.report-resumen {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
