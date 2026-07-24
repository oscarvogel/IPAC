<template>
  <section class="cash-screen">
    <CajaHero
      :caja-hoy="cajaHoy"
      :fallback-sucursal="auth.user?.perfil?.sucursal?.nombre"
      :puede-mover="puedeMover"
      @print="printCajaResumen"
      @movimiento="openMovimiento"
      @cerrar="openCerrar"
    />

    <div class="stats-grid cash-stats">
      <article class="stat-card">
        <span>Total esperado</span>
        <strong>$ {{ formatMoney(cajaTotales.total) }}</strong>
        <small>incluye pagos y movimientos</small>
      </article>
      <article class="stat-card">
        <span>Efectivo</span>
        <strong>$ {{ formatMoney(cajaTotales.efectivo) }}</strong>
        <small>saldo de efectivo</small>
      </article>
      <article class="stat-card">
        <span>Transferencia</span>
        <strong>$ {{ formatMoney(cajaTotales.transferencia) }}</strong>
        <small>pagos bancarios</small>
      </article>
      <article class="stat-card">
        <span>Movimientos</span>
        <strong>{{ cajaMovimientos.length }}</strong>
        <small>registrados hoy</small>
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
