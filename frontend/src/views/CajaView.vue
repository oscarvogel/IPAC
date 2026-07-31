<template>
  <section class="cash-workspace text-text-primary">
    <CajaHero
      :caja-hoy="cajaHoy"
      :fallback-sucursal="auth.user?.perfil?.sucursal?.nombre"
      :puede-mover="puedeMover"
      @print="printCajaResumen"
      @movimiento="openMovimiento"
      @cerrar="openCerrar"
    />

    <div class="cash-metrics-grid">
      <article
        v-for="(stat, index) in stats"
        :key="stat.label"
        class="cash-metric-card border-border bg-surface"
        :class="{ 'cash-metric-card-featured': index === 0 }"
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
      :total-esperado="cajaTotales.total"
      :loading="loading"
      @close="showCerrar = false"
      @submit="submitCerrar"
    />
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  ArrowsRightLeftIcon,
  BanknotesIcon,
  BuildingLibraryIcon,
  WalletIcon,
} from '@heroicons/vue/24/outline'
import { useAuth } from '@/composables/useAuth'
import { useCaja } from '@/composables/useCaja'
import { useToast } from '@/composables/useToast'
import { formatMoney } from '@/lib/formatters'
import CajaHero from '@/components/caja/CajaHero.vue'
import CajaMovimientos from '@/components/caja/CajaMovimientos.vue'
import CajaPrintSummary from '@/components/caja/CajaPrintSummary.vue'
import MovimientoForm from '@/components/caja/MovimientoForm.vue'
import CerrarCajaModal from '@/components/caja/CerrarCajaModal.vue'

const auth = useAuth()
const caja = useCaja()
const toast = useToast()

const { cajaHoy, cajaMovimientos, cajaTotales, loading } = caja

const showMovimiento = ref(false)
const showCerrar = ref(false)
const movimientoTipoInicial = ref('egreso')

const puedeMover = computed(() => cajaHoy.value && cajaHoy.value.estado !== 'cerrada')

const stats = computed(() => [
  {
    label: 'Total esperado',
    value: `$ ${formatMoney(cajaTotales.value.total, { fractionDigits: 2 })}`,
    detail: 'balance operativo del día',
    tone: 'primary',
    icon: WalletIcon,
  },
  {
    label: 'Efectivo',
    value: `$ ${formatMoney(cajaTotales.value.efectivo, { fractionDigits: 2 })}`,
    detail: 'disponible en caja',
    tone: 'success',
    icon: BanknotesIcon,
  },
  {
    label: 'Transferencias',
    value: `$ ${formatMoney(cajaTotales.value.transferencia, { fractionDigits: 2 })}`,
    detail: 'operaciones bancarias',
    tone: 'info',
    icon: BuildingLibraryIcon,
  },
  {
    label: 'Movimientos',
    value: cajaMovimientos.value.length,
    detail: 'registrados en la jornada',
    tone: 'warning',
    icon: ArrowsRightLeftIcon,
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

async function submitCerrar(totalContado) {
  try {
    await caja.cerrarCaja(totalContado)
    showCerrar.value = false
    toast.success('Caja cerrada.')
  } catch (err) {
    toast.error(err.message || 'No se pudo cerrar la caja.')
  }
}

function printCajaResumen() {
  window.print()
}

onMounted(() => {
  caja.loadCajaHoy()
})
</script>
