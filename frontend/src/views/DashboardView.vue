<template>
  <section class="dashboard-screen text-text-primary">
    <div class="stats-grid">
      <article
        v-for="(stat, index) in stats"
        :key="stat.label"
        class="stat-card border-border bg-surface"
        :class="{ 'stat-card-featured': index === 0 }"
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
          <p v-if="!ultimosPagos.length" class="dashboard-empty-state">
            Todavía no hay pagos en el mes.
          </p>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  BanknotesIcon,
  BuildingStorefrontIcon,
  ChevronRightIcon,
  CreditCardIcon,
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

const auth = useAuth()
const caja = useCaja()
const { sucursales, loadCatalogos } = useCatalogos()
const { selectedSucursalId } = useDashboardFilters()

const alumnosCount = ref(0)
const pagosMes = ref([])
const ultimosPagos = computed(() => pagosMes.value.slice(0, 5))
const totalCobradoMes = computed(() =>
  pagosMes.value.reduce((sum, pago) => sum + Number(pago.importe || 0), 0),
)

const { cajaHoy, cajaMovimientos, loadCajaHoy } = caja
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

onMounted(async () => {
  await loadCatalogos()
  if (!selectedSucursalId.value && sucursales.value.length) {
    const preferred = auth.user.value?.perfil?.sucursal?.id
    selectedSucursalId.value = String(
      sucursales.value.find((sucursal) => sucursal.id === preferred)?.id
      || sucursales.value[0].id,
    )
  }
  await cargarDashboard()
})

watch(selectedSucursalId, () => {
  cargarDashboard()
})

async function cargarDashboard() {
  const sucursalId = selectedSucursalId.value || null
  await Promise.all([cargarResumen(sucursalId), loadCajaHoy(sucursalId)])
}

async function cargarResumen(sucursalId) {
  const hoy = new Date()
  const primero = new Date(hoy.getFullYear(), hoy.getMonth(), 1)
  const iso = (date) => date.toISOString().slice(0, 10)
  const [alumnos, pagos] = await Promise.all([
    apiRequest('/alumnos/'),
    apiRequest('/pagos/', {
      query: { desde: iso(primero), hasta: iso(hoy), sucursal: sucursalId },
    }),
  ])
  const alumnosFiltrados = sucursalId
    ? (alumnos.results || []).filter(
      (alumno) => String(alumno.sucursal) === String(sucursalId),
    )
    : (alumnos.results || [])
  alumnosCount.value = alumnosFiltrados.length
  pagosMes.value = pagos.results || []
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
    detail: `${pagosMes.value.length} pagos`,
    tone: 'green',
    icon: BanknotesIcon,
  },
  {
    label: 'Pagos del mes',
    value: pagosMes.value.length,
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
