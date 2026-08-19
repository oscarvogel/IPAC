<template>
  <section class="dashboard-screen text-text-primary">
    <AppPageState
      v-if="!pageReady"
      :loading="!pageError"
      :error="pageError"
      label="el dashboard"
      @retry="loadPage"
    />
    <template v-else>
    <div class="stats-grid">
      <article
        v-for="stat in stats"
        :key="stat.label"
        class="stat-card border-border bg-surface"
      >
        <span class="stat-icon" :class="`stat-icon-${stat.tone}`">
          <component :is="stat.icon" aria-hidden="true" />
        </span>
        <span class="stat-copy">
          <span class="stat-label">{{ stat.label }}</span>
          <strong>{{ stat.value }}</strong>
          <small>{{ stat.detail }}</small>
        </span>
      </article>
    </div>

    <div class="dashboard-grid">
      <article class="panel cash-card border-border bg-surface">
        <div class="cash-card-head">
          <span class="section-icon section-icon-gold">
            <WalletIcon aria-hidden="true" />
          </span>
          <div>
            <p class="eyebrow">Caja del día</p>
            <h2>{{ cajaTitle }}</h2>
            <p class="cash-status">
              <span>{{ cajaDate }}</span>
              <span v-if="cajaHoy" class="status-dot" />
              <strong v-if="cajaHoy">{{ cajaStatus }}</strong>
            </p>
          </div>
        </div>

        <div class="dashboard-caja-body">
          <div class="cash-metric">
            <span>Total esperado</span>
            <strong>$ {{ formatMoney(cajaTotalEsperado, { fractionDigits: 2 }) }}</strong>
          </div>
          <div class="cash-metric">
            <span>Movimientos</span>
            <strong>{{ cajaMovimientos.length }}</strong>
          </div>
          <router-link to="/caja" class="cash-cta bg-primary hover:bg-primary-hover">
            <WalletIcon aria-hidden="true" />
            <span>Ir a caja</span>
          </router-link>
        </div>
      </article>

      <article class="panel payments-card border-border bg-surface">
        <div class="payments-card-head">
          <div class="payments-title">
            <span class="section-icon section-icon-violet">
              <ReceiptPercentIcon aria-hidden="true" />
            </span>
            <div>
              <h2>Últimos pagos</h2>
              <p>{{ ultimosPagos.length }} del mes en curso</p>
            </div>
          </div>
          <router-link to="/reportes" class="view-all-link">
            <span>Ver todos</span>
            <ChevronRightIcon aria-hidden="true" />
          </router-link>
        </div>

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
              <tr v-for="pago in ultimosPagos" :key="pago.id">
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
          <div v-if="!ultimosPagos.length" class="dashboard-empty-state">
            <span><DocumentMagnifyingGlassIcon aria-hidden="true" /></span>
            <strong>Todavía no hay pagos este mes</strong>
            <p>Las próximas cobranzas aparecerán acá automáticamente.</p>
          </div>
        </div>
      </article>
    </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  BanknotesIcon,
  BuildingStorefrontIcon,
  ChevronRightIcon,
  CreditCardIcon,
  DocumentMagnifyingGlassIcon,
  EllipsisVerticalIcon,
  ReceiptPercentIcon,
  UserGroupIcon,
  WalletIcon,
} from '@heroicons/vue/24/outline'
import { useAuth } from '@/composables/useAuth'
import { useCaja } from '@/composables/useCaja'
import { useCatalogos } from '@/composables/useCatalogos'
import { useDashboardFilters } from '@/composables/useDashboardFilters'
import { apiRequest } from '@/lib/api'
import { formatDate, formatMoney } from '@/lib/formatters'
import { useToast } from '@/composables/useToast'
import AppPageState from '@/components/ui/AppPageState.vue'

const auth = useAuth()
const caja = useCaja()
const toast = useToast()
const { sucursales, loadCatalogos } = useCatalogos()
const { selectedSucursalId } = useDashboardFilters()

const alumnosCount = ref(0)
const pagosMes = ref([])
const pagosMesCount = ref(0)
const totalCobradoMes = ref(0)
const pageReady = ref(false)
const pageError = ref('')
const ultimosPagos = computed(() => pagosMes.value.slice(0, 5))

const { cajaHoy, cajaMovimientos, error: cajaError, loadCajaHoy } = caja
const cajaTotalEsperado = computed(() =>
  cajaMovimientos.value.reduce((total, movimiento) => {
    const amount = Number(movimiento.importe || 0)
    const signed = ['egreso', 'retiro', 'pase'].includes(movimiento.tipo) ? -amount : amount
    return total + signed
  }, 0),
)

const cajaTitle = computed(() => {
  if (!cajaHoy.value) return 'Sin caja abierta'
  return cajaHoy.value.sucursal_nombre || auth.user.value?.perfil?.sucursal?.nombre || 'Caja'
})

const cajaDate = computed(() => (
  cajaHoy.value?.fecha ? formatDate(cajaHoy.value.fecha) : 'Sin actividad para hoy'
))

const cajaStatus = computed(() => (
  cajaHoy.value?.estado === 'abierta' ? 'abierta' : cajaHoy.value?.estado || ''
))

onMounted(loadPage)

watch(selectedSucursalId, () => {
  if (pageReady.value) refreshDashboard()
})

async function loadPage() {
  pageReady.value = false
  pageError.value = ''
  try {
    await loadCatalogos()
    if (!selectedSucursalId.value && sucursales.value.length) {
      const preferred = auth.user.value?.perfil?.sucursal?.id
      selectedSucursalId.value = String(
        sucursales.value.find((sucursal) => sucursal.id === preferred)?.id
        || sucursales.value[0].id,
      )
    }
    await cargarDashboard()
    if (cajaError.value) throw new Error(cajaError.value)
    pageReady.value = true
  } catch (err) {
    pageError.value = err.message || 'No se pudo cargar el resumen del dashboard.'
  }
}

async function refreshDashboard() {
  try {
    await cargarDashboard()
    if (cajaError.value) throw new Error(cajaError.value)
  } catch (err) {
    toast.error(err.message || 'No se pudo actualizar el dashboard.')
  }
}

async function cargarDashboard() {
  const sucursalId = selectedSucursalId.value || null
  await Promise.all([cargarResumen(sucursalId), loadCajaHoy(sucursalId)])
}

async function cargarResumen(sucursalId) {
  const hoy = new Date()
  const primero = new Date(hoy.getFullYear(), hoy.getMonth(), 1)
  const iso = (date) => date.toISOString().slice(0, 10)
  const [alumnos, pagos, resumen] = await Promise.all([
    apiRequest('/alumnos/', { query: { sucursal: sucursalId } }),
    apiRequest('/pagos/', {
      query: { desde: iso(primero), hasta: iso(hoy), sucursal: sucursalId },
    }),
    apiRequest('/reportes/resumen/', {
      query: { desde: iso(primero), hasta: iso(hoy), sucursal: sucursalId },
    }),
  ])
  alumnosCount.value = Number(alumnos.count || 0)
  pagosMes.value = pagos.results || []
  pagosMesCount.value = Number(resumen.cobranzas?.cantidad_pagos || 0)
  totalCobradoMes.value = Number(resumen.cobranzas?.total || 0)
}

const stats = computed(() => [
  {
    label: 'Alumnos',
    value: alumnosCount.value,
    detail: 'base cargada',
    tone: 'gold',
    icon: UserGroupIcon,
  },
  {
    label: 'Sucursales',
    value: sucursales.value.length,
    detail: sucursales.value.map((sucursal) => sucursal.nombre).join(' y '),
    tone: 'blue',
    icon: BuildingStorefrontIcon,
  },
  {
    label: 'Cobrado del mes',
    value: `$ ${formatMoney(totalCobradoMes.value, { fractionDigits: 2 })}`,
    detail: `${pagosMesCount.value} pagos`,
    tone: 'green',
    icon: BanknotesIcon,
  },
  {
    label: 'Pagos del mes',
    value: pagosMesCount.value,
    detail: 'filtrados por período actual',
    tone: 'violet',
    icon: CreditCardIcon,
  },
])

function paymentLabel(medio) {
  const labels = {
    efectivo: 'efectivo',
    transferencia: 'transferencia',
    tarjeta: 'tarjeta',
    otro: 'otro',
  }
  return labels[medio] || medio || 'otro'
}

function paymentIcon(medio) {
  return medio === 'tarjeta' ? CreditCardIcon : BanknotesIcon
}
</script>
