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
    <div id="dashboard-indicators" class="stats-grid" :class="{ 'show-all-mobile-stats': showAllMobileStats }">
      <component
        v-for="stat in stats"
        :key="stat.label"
        :is="stat.to ? 'RouterLink' : 'article'"
        :to="stat.to"
        class="stat-card border-border bg-surface"
        :class="{ 'stat-card-secondary': !stat.mobilePrimary }"
      >
        <span class="stat-icon" :class="`stat-icon-${stat.tone}`">
          <component :is="stat.icon" aria-hidden="true" />
        </span>
        <span class="stat-copy">
          <span class="stat-label">{{ stat.label }}</span>
          <strong>{{ stat.value }}</strong>
          <small>{{ stat.detail }}</small>
          <span v-if="stat.action" class="stat-action">
            <span>{{ stat.action }}</span>
            <ArrowRightIcon aria-hidden="true" />
          </span>
        </span>
      </component>
    </div>
    <button
      type="button"
      class="dashboard-stats-toggle"
      aria-controls="dashboard-indicators"
      :aria-expanded="showAllMobileStats"
      @click="showAllMobileStats = !showAllMobileStats"
    >
      <span>{{ showAllMobileStats ? 'Ver menos indicadores' : 'Ver más indicadores' }}</span>
      <ChevronDownIcon aria-hidden="true" />
    </button>

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

        <DashboardRecentPayments :pagos="ultimosPagos" />
      </article>
    </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  ArrowRightIcon,
  BanknotesIcon,
  BuildingStorefrontIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  CreditCardIcon,
  LockClosedIcon,
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
import DashboardRecentPayments from '@/components/dashboard/DashboardRecentPayments.vue'

const auth = useAuth()
const caja = useCaja()
const toast = useToast()
const { sucursales, loadCatalogos } = useCatalogos()
const { selectedSucursalId } = useDashboardFilters()

const alumnosCount = ref(0)
const pagosMes = ref([])
const pagosMesCount = ref(0)
const totalCobradoMes = ref(0)
const cobradoHoy = ref(0)
const deudaTotal = ref(0)
const saldoFavor = ref(0)
const alumnosConDeuda = ref(0)
const cuotasVencidas = ref(0)
const cobrosPorMedio = ref({})
const cobrosPorSucursal = ref([])
const cajasPeriodo = ref({ abiertas: 0, cerradas: 0, diferencia_acumulada: 0 })
const pageReady = ref(false)
const pageError = ref('')
const showAllMobileStats = ref(false)
const ultimosPagos = computed(() => pagosMes.value.slice(0, 5))

const { cajaHoy, cajaMovimientos, error: cajaError, loadCajaHoy } = caja
const cajaTotalEsperado = computed(() => Number(cajaHoy.value?.resumen?.efectivo_esperado || 0))

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
  const [alumnos, pagos, resumen, resumenInstitucion] = await Promise.all([
    apiRequest('/alumnos/', { query: { sucursal: sucursalId } }),
    apiRequest('/pagos/', {
      query: { desde: iso(primero), hasta: iso(hoy), sucursal: sucursalId },
    }),
    apiRequest('/reportes/resumen/', {
      query: { desde: iso(primero), hasta: iso(hoy), sucursal: sucursalId },
    }),
    apiRequest('/reportes/resumen/', {
      query: { desde: iso(primero), hasta: iso(hoy) },
    }),
  ])
  alumnosCount.value = Number(alumnos.count || 0)
  pagosMes.value = pagos.results || []
  pagosMesCount.value = Number(resumen.cobranzas?.cantidad_pagos || 0)
  totalCobradoMes.value = Number(resumen.cobranzas?.total || 0)
  cobradoHoy.value = Number(resumen.cobranzas?.hoy || 0)
  deudaTotal.value = Number(resumen.cuenta_corriente?.deuda || 0)
  saldoFavor.value = Number(resumen.cuenta_corriente?.saldo_a_favor || 0)
  alumnosConDeuda.value = Number(resumen.cuenta_corriente?.alumnos_con_deuda || 0)
  cuotasVencidas.value = Number(resumen.cuenta_corriente?.cuotas_vencidas || 0)
  cobrosPorMedio.value = resumen.cobranzas?.por_medio || {}
  cobrosPorSucursal.value = resumenInstitucion.cobranzas?.por_sucursal || []
  cajasPeriodo.value = resumen.cajas || cajasPeriodo.value
}

const medioPrincipal = computed(() => {
  const labels = { efectivo: 'Efectivo', transferencia: 'Transferencia', mercado_pago: 'Mercado Pago', tarjeta: 'Tarjeta', otro: 'Otros' }
  const [medio, importe] = Object.entries(cobrosPorMedio.value).sort((a, b) => Number(b[1]) - Number(a[1]))[0] || ['—', 0]
  return { nombre: labels[medio] || medio, importe: Number(importe || 0) }
})

const sucursalPrincipal = computed(() => {
  const row = [...cobrosPorSucursal.value].sort((a, b) => Number(b.total) - Number(a.total))[0]
  return row ? { nombre: row.sucursal__nombre, total: Number(row.total || 0) } : null
})

const stats = computed(() => [
  {
    label: 'Alumnos',
    mobilePrimary: true,
    action: 'Ver alumnos',
    value: alumnosCount.value,
    detail: 'base cargada',
    tone: 'gold',
    icon: UserGroupIcon,
    to: '/alumnos',
  },
  {
    label: 'Sucursales',
    action: auth.can('manage-branches') ? 'Ver sucursales' : undefined,
    value: sucursales.value.length,
    detail: sucursales.value.map((sucursal) => sucursal.nombre).join(' y '),
    tone: 'blue',
    icon: BuildingStorefrontIcon,
    to: auth.can('manage-branches') ? '/configuracion' : null,
  },
  {
    label: 'Cobrado del mes',
    mobilePrimary: true,
    action: 'Ver cobranzas',
    value: `$ ${formatMoney(totalCobradoMes.value, { fractionDigits: 2 })}`,
    detail: `${pagosMesCount.value} pagos`,
    tone: 'green',
    icon: BanknotesIcon,
    to: '/reportes',
  },
  {
    label: 'Pagos del mes',
    action: 'Ver pagos',
    value: pagosMesCount.value,
    detail: 'filtrados por período actual',
    tone: 'violet',
    icon: CreditCardIcon,
    to: '/reportes',
  },
  {
    label: 'Cobrado hoy',
    mobilePrimary: true,
    action: 'Ver cobranzas',
    value: `$ ${formatMoney(cobradoHoy.value, { fractionDigits: 2 })}`,
    detail: 'cobranzas del día',
    tone: 'green',
    icon: BanknotesIcon,
    to: '/reportes',
  },
  {
    label: 'Deuda pendiente',
    mobilePrimary: true,
    action: 'Gestionar deuda',
    value: `$ ${formatMoney(deudaTotal.value, { fractionDigits: 2 })}`,
    detail: `${alumnosConDeuda.value} alumnos · ${cuotasVencidas.value} cuotas vencidas`,
    tone: 'gold',
    icon: WalletIcon,
    to: '/deudores',
  },
  {
    label: 'Saldo a favor',
    action: 'Ver reportes',
    value: `$ ${formatMoney(saldoFavor.value, { fractionDigits: 2 })}`,
    detail: 'crédito disponible de alumnos',
    tone: 'blue',
    icon: CreditCardIcon,
    to: '/reportes',
  },
  {
    label: 'Medio principal',
    action: 'Ver reportes',
    value: medioPrincipal.value.nombre,
    detail: `$ ${formatMoney(medioPrincipal.value.importe, { fractionDigits: 2 })} del mes`,
    tone: 'violet',
    icon: CreditCardIcon,
    to: '/reportes',
  },
  ...(cobrosPorSucursal.value.length > 1 && sucursalPrincipal.value ? [{
    label: 'Sucursal con mayor cobro',
    action: 'Ver reportes',
    value: sucursalPrincipal.value.nombre,
    detail: `$ ${formatMoney(sucursalPrincipal.value.total, { fractionDigits: 2 })} del mes`,
    tone: 'blue',
    icon: BuildingStorefrontIcon,
    to: '/reportes',
  }] : []),
  {
    label: 'Cajas del período',
    action: 'Ver cajas',
    value: `${cajasPeriodo.value.abiertas || 0} abiertas`,
    detail: `${cajasPeriodo.value.cerradas || 0} cerradas · diferencia $ ${formatMoney(cajasPeriodo.value.diferencia_acumulada || 0)}`,
    tone: 'gold',
    icon: LockClosedIcon,
    to: '/reportes',
  },
])

</script>
