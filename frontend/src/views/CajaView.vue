<template>
  <section class="cash-workspace text-text-primary">
    <AppPageState
      v-if="!pageReady"
      :loading="!pageError"
      :error="pageError"
      label="la caja"
      @retry="loadPage"
    />
    <template v-else>
    <CajaHero
      :caja-hoy="cajaHoy"
      :fallback-sucursal="auth.user?.perfil?.sucursal?.nombre"
      :puede-mover="puedeMover"
      @print="printCajaResumen"
      @movimiento="openMovimiento"
      @cerrar="openCerrar"
    />

    <section v-if="saldoAnterior" class="cash-carry-banner border-border bg-surface" aria-live="polite">
      <div>
        <p class="eyebrow">Saldo disponible de cierre anterior</p>
        <strong>$ {{ formatMoney(saldoAnterior.importe, { fractionDigits: 2 }) }}</strong>
        <span>Origen: {{ formatDate(saldoAnterior.fecha_origen) }} · {{ saldoAnterior.usuario_origen }}</span>
      </div>
      <button class="primary-button" type="button" :disabled="loading" @click="applyPreviousBalance">
        Usar como saldo inicial
      </button>
    </section>

    <section class="cash-summary-section" aria-labelledby="cash-physical-title">
      <header class="cash-summary-heading">
        <div>
          <p class="eyebrow">Conciliación</p>
          <h2 id="cash-physical-title">Efectivo físico</h2>
        </div>
        <span>No incluye transferencias ni otros medios electrónicos.</span>
      </header>
      <div class="cash-metrics-grid cash-metrics-grid-physical">
      <article
        v-for="stat in physicalStats"
        :key="stat.label"
        class="cash-metric-card border-border bg-surface"
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
    </section>

    <section class="cash-summary-section" aria-labelledby="cash-noncash-title">
      <header class="cash-summary-heading">
        <div>
          <p class="eyebrow">Cobranzas de la jornada</p>
          <h2 id="cash-noncash-title">Total cobrado y medios no efectivos</h2>
        </div>
        <strong>$ {{ formatMoney(cajaTotales.totalCobrado, { fractionDigits: 2 }) }}</strong>
      </header>
      <div class="cash-metrics-grid cash-metrics-grid-noncash">
        <article
          v-for="stat in nonCashStats"
          :key="stat.label"
          class="cash-metric-card cash-metric-card-compact border-border bg-surface"
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
    </section>

    <CajaMovimientos :movimientos="cajaMovimientos" />

    <CajaPrintSummary
      :caja-hoy="cajaHoy"
      :movimientos="cajaMovimientos"
      :caja-totales="cajaTotales"
      :username="auth.user?.username || ''"
      :fallback-sucursal="auth.user?.perfil?.sucursal?.nombre"
    />

    <MovimientoForm
      v-if="showMovimiento"
      :caja-hoy="cajaHoy"
      :loading="loading"
      :tipo-inicial="movimientoTipoInicial"
      @close="closeMovimiento"
      @submit="submitMovimiento"
    />

    <CerrarCajaModal
      v-if="showCerrar"
      :caja-hoy="cajaHoy"
      :total-esperado="cajaTotales.efectivoEsperado"
      :loading="loading"
      @close="showCerrar = false"
      @submit="submitCerrar"
    />
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowsRightLeftIcon,
  BanknotesIcon,
  BuildingLibraryIcon,
  CreditCardIcon,
  DevicePhoneMobileIcon,
  EllipsisHorizontalCircleIcon,
  WalletIcon,
} from '@heroicons/vue/24/outline'
import { useAuth } from '@/composables/useAuth'
import { useCaja } from '@/composables/useCaja'
import { useToast } from '@/composables/useToast'
import { formatDate, formatMoney } from '@/lib/formatters'
import CajaHero from '@/components/caja/CajaHero.vue'
import CajaMovimientos from '@/components/caja/CajaMovimientos.vue'
import CajaPrintSummary from '@/components/caja/CajaPrintSummary.vue'
import MovimientoForm from '@/components/caja/MovimientoForm.vue'
import CerrarCajaModal from '@/components/caja/CerrarCajaModal.vue'
import AppPageState from '@/components/ui/AppPageState.vue'

const auth = useAuth()
const caja = useCaja()
const toast = useToast()
const route = useRoute()
const router = useRouter()

const { cajaHoy, saldoAnterior, cajaMovimientos, cajaTotales, loading, error: cajaError } = caja

const showMovimiento = ref(false)
const showCerrar = ref(false)
const movimientoTipoInicial = ref('egreso')
const pageReady = ref(false)
const pageError = ref('')

const puedeMover = computed(() => auth.can('operate-cash')
  && cajaHoy.value
  && cajaHoy.value.estado !== 'cerrada')

const physicalStats = computed(() => [
  {
    label: 'Saldo inicial',
    value: `$ ${formatMoney(cajaTotales.value.saldoInicial, { fractionDigits: 2 })}`,
    detail: 'recibido del cierre anterior',
    tone: 'primary',
    icon: WalletIcon,
  },
  {
    label: 'Cobros en efectivo',
    value: `$ ${formatMoney(cajaTotales.value.cobranzasEfectivo, { fractionDigits: 2 })}`,
    detail: 'cobranzas de la jornada',
    tone: 'success',
    icon: BanknotesIcon,
  },
  {
    label: 'Efectivo esperado',
    value: `$ ${formatMoney(cajaTotales.value.efectivoEsperado, { fractionDigits: 2 })}`,
    detail: 'saldo inicial + entradas − salidas',
    tone: 'info',
    icon: WalletIcon,
  },
  {
    label: cajaHoy.value?.estado === 'cerrada' ? 'Saldo final físico' : 'Salidas de efectivo',
    value: `$ ${formatMoney(
      cajaHoy.value?.estado === 'cerrada'
        ? cajaTotales.value.saldoFinalFisico
        : cajaTotales.value.egresosEfectivo + cajaTotales.value.retirosEfectivo,
      { fractionDigits: 2 },
    )}`,
    detail: cajaHoy.value?.estado === 'cerrada' ? 'efectivo contado al cierre' : 'egresos y retiros',
    tone: 'warning',
    icon: ArrowsRightLeftIcon,
  },
])

const nonCashStats = computed(() => [
  {
    label: 'Transferencias',
    value: `$ ${formatMoney(cajaTotales.value.transferencia, { fractionDigits: 2 })}`,
    detail: 'no integra el efectivo físico',
    tone: 'info',
    icon: BuildingLibraryIcon,
  },
  {
    label: 'Mercado Pago',
    value: `$ ${formatMoney(cajaTotales.value.mercadoPago, { fractionDigits: 2 })}`,
    detail: 'cobros por billetera digital',
    tone: 'success',
    icon: DevicePhoneMobileIcon,
  },
  {
    label: 'Tarjetas',
    value: `$ ${formatMoney(cajaTotales.value.tarjeta, { fractionDigits: 2 })}`,
    detail: 'crédito y débito',
    tone: 'primary',
    icon: CreditCardIcon,
  },
  {
    label: 'Otros medios',
    value: `$ ${formatMoney(cajaTotales.value.otro, { fractionDigits: 2 })}`,
    detail: `${cajaMovimientos.value.length} movimientos totales`,
    tone: 'warning',
    icon: EllipsisHorizontalCircleIcon,
  },
])

function openMovimiento(tipo = 'egreso') {
  movimientoTipoInicial.value = tipo
  showMovimiento.value = true
}

function closeMovimiento() {
  showMovimiento.value = false
}

async function submitMovimiento(payload) {
  try {
    await caja.createMovimiento(payload)
    closeMovimiento()
    toast.success('Movimiento registrado.')
  } catch (err) {
    toast.error(err.message || 'No se pudo registrar el movimiento.')
  }
}

function openCerrar() {
  showCerrar.value = true
}

async function submitCerrar(cierre) {
  try {
    await caja.cerrarCaja(cierre)
    showCerrar.value = false
    toast.success('Caja cerrada.')
  } catch (err) {
    toast.error(err.message || 'No se pudo cerrar la caja.')
  }
}

function printCajaResumen() {
  window.print()
}

onMounted(loadPage)

watch(
  [pageReady, () => route.query.accion],
  ([ready, accion]) => {
    if (!ready || !accion) return
    consumeRouteAction(accion)
  },
  { immediate: true },
)

async function loadPage() {
  pageReady.value = false
  pageError.value = ''
  await caja.loadCajaHoy()
  if (cajaError.value) {
    pageError.value = cajaError.value
    return
  }
  pageReady.value = true
}

async function applyPreviousBalance() {
  try {
    await caja.aplicarSaldoAnterior()
    toast.success('Saldo anterior aplicado como saldo inicial.')
  } catch (err) {
    toast.error(err.message || 'No se pudo aplicar el saldo anterior.')
  }
}

function consumeRouteAction(accion) {
  const { accion: _discarded, ...query } = route.query
  router.replace({ path: route.path, query, hash: route.hash })

  const movementActions = ['ingreso', 'egreso', 'retiro']
  const validAction = movementActions.includes(accion) || accion === 'cerrar'
  if (!validAction || !auth.can('operate-cash')) return

  if (!puedeMover.value) {
    toast.error('La caja del día debe estar abierta para realizar esta operación.')
    return
  }

  if (accion === 'cerrar') openCerrar()
  else openMovimiento(accion)
}
</script>
