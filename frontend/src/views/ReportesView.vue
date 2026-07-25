<template>
  <section class="reports-screen">
    <div class="stats-grid">
      <article v-for="stat in stats" :key="stat.label" class="stat-card">
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
        <small>{{ stat.detail }}</small>
      </article>
    </div>

    <div class="topbar-filters">
      <label>
        <span>Desde</span>
        <input v-model="filtros.desde" type="date" />
      </label>
      <label>
        <span>Hasta</span>
        <input v-model="filtros.hasta" type="date" />
      </label>
      <label>
        <span>Sucursal</span>
        <select v-model="filtros.sucursal" class="compact-select">
          <option value="">Todas</option>
          <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
            {{ sucursal.nombre }}
          </option>
        </select>
      </label>
      <label>
        <span>Medio</span>
        <select v-model="filtros.medio" class="compact-select">
          <option value="">Todos</option>
          <option value="efectivo">Efectivo</option>
          <option value="transferencia">Transferencia</option>
          <option value="tarjeta">Tarjeta</option>
          <option value="otro">Otro</option>
        </select>
      </label>
      <button class="primary-button" type="button" :disabled="loading" @click="aplicarFiltros">
        {{ loading ? 'Cargando...' : 'Aplicar filtros' }}
      </button>
      <button class="secondary-button" type="button" :disabled="loading" @click="exportarCsv">
        Exportar CSV
      </button>
    </div>

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
  </section>
</template>

<script setup>
import { computed, onMounted, reactive } from 'vue'
import { useCatalogos } from '@/composables/useCatalogos'
import { useReportes } from '@/composables/useReportes'
import { useToast } from '@/composables/useToast'
import { formatDate, formatMoney } from '@/lib/formatters'

const { sucursales, loadCatalogos } = useCatalogos()
const { resumen, pagos, loading, loadResumen, loadPagos, exportarCsv: descargarCsv } = useReportes()
const toast = useToast()

const filtros = reactive({
  desde: '',
  hasta: '',
  sucursal: '',
  medio: '',
})

function rangoPorDefecto() {
  // Periodo por defecto: del 1ro del mes actual hasta hoy.
  const hoy = new Date()
  const primero = new Date(hoy.getFullYear(), hoy.getMonth(), 1)
  const iso = (d) => d.toISOString().slice(0, 10)
  return { desde: iso(primero), hasta: iso(hoy) }
}

onMounted(async () => {
  Object.assign(filtros, rangoPorDefecto())
  await loadCatalogos()
  await aplicarFiltros()
})

const totalCobrado = computed(
  () => Number(resumen.value?.cobranzas?.total || 0),
)
const cantidadPagos = computed(
  () => resumen.value?.cobranzas?.cantidad_pagos ?? 0,
)
const deudaNeta = computed(
  () => Number(resumen.value?.cuenta_corriente?.saldo_neto || 0),
)
const cajasCerradas = computed(
  () => resumen.value?.cajas?.cerradas ?? 0,
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

async function aplicarFiltros() {
  const payload = {
    desde: filtros.desde || undefined,
    hasta: filtros.hasta || undefined,
    sucursal: filtros.sucursal || undefined,
    medio: filtros.medio || undefined,
  }
  await Promise.all([loadResumen(payload), loadPagos(payload)])
}

async function exportarCsv() {
  const payload = {
    desde: filtros.desde || undefined,
    hasta: filtros.hasta || undefined,
    sucursal: filtros.sucursal || undefined,
    medio: filtros.medio || undefined,
  }
  try {
    await descargarCsv(payload)
  } catch (err) {
    toast.error(err.message || 'No se pudo generar el CSV.')
  }
}
</script>

<style scoped>
.topbar-filters {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.topbar-filters label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.85rem;
  color: #4a4a55;
}

.topbar-filters input,
.topbar-filters select {
  min-width: 140px;
}
</style>
