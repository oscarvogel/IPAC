<template>
  <section class="transfer-workspace text-text-primary" :aria-busy="loading" aria-labelledby="transferencias-title">
    <header class="transfer-page-heading">
      <div><p class="eyebrow">Caja y Tesorería</p><h1 id="transferencias-title">Transferencias entre cajas</h1><p>Administrá traspasos de efectivo entre las cajas disponibles en tu alcance.</p></div>
      <button class="secondary-button" type="button" :disabled="loading || Boolean(pendiente)" @click="load">Actualizar</button>
    </header>
    <p v-if="loading" role="status">{{ pendiente ? 'Registrando transferencia…' : 'Cargando cajas e historial…' }}</p>
    <section v-if="error" class="transfer-error" role="alert">
      <p>{{ error }}</p><button class="secondary-button" type="button" :disabled="loading || Boolean(pendiente)" @click="load">Reintentar consulta</button>
    </section>
    <section v-if="comprobante" class="transfer-receipt border-border bg-surface" role="status" aria-live="polite">
      <p class="eyebrow">Transferencia registrada</p><h2>Comprobante {{ comprobante.numero_comprobante }}</h2>
      <p>$ {{ formatMoney(comprobante.importe, { fractionDigits: 2 }) }} · {{ comprobante.origen.sucursal_nombre }} → {{ comprobante.destino.sucursal_nombre }}</p>
      <p>El efectivo fue descontado del origen y acreditado al destino.</p>
    </section>
    <p v-if="!loading && !error && cajasAbiertas.length < 2" class="transfer-empty" role="status">
      {{ cajasAbiertas.length ? 'Hay una sola caja abierta disponible.' : 'No hay cajas abiertas disponibles.' }} Necesitás dos cajas abiertas para hoy dentro de tu alcance para transferir.
    </p>
    <TransferenciaCajaForm v-if="cajasAbiertas.length >= 2" :key="formVersion" :cajas="cajasAbiertas" :loading="loading || Boolean(pendiente)" @review="pendiente = $event" />
    <TransferenciasCajaHistorial v-if="(!loading && !error) || transferencias.length" :transferencias="transferencias" />
    <ConfirmDialog :open="Boolean(pendiente)" title="Confirmar transferencia entre cajas" :description="resumenConfirmacion" confirm-label="Confirmar transferencia" tone="warning" :loading="loading" @cancel="pendiente = null" @confirm="confirmar" />
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useTransferenciasCaja } from '@/composables/useTransferenciasCaja'
import { formatMoney } from '@/lib/formatters'
import TransferenciaCajaForm from '@/components/caja/TransferenciaCajaForm.vue'
import TransferenciasCajaHistorial from '@/components/caja/TransferenciasCajaHistorial.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'

const { cajasAbiertas, transferencias, loading, error, load, transferir } = useTransferenciasCaja()
const pendiente = ref(null)
const comprobante = ref(null)
const formVersion = ref(0)
const resumenConfirmacion = computed(() => {
  if (!pendiente.value) return ''
  const origen = cajasAbiertas.value.find((caja) => caja.id === pendiente.value.origen_id)
  const destino = cajasAbiertas.value.find((caja) => caja.id === pendiente.value.destino_id)
  return 'Origen: ' + origen?.sucursal_nombre + ' · ' + origen?.usuario_nombre + ' · Caja #' + origen?.id
    + '. Destino: ' + destino?.sucursal_nombre + ' · ' + destino?.usuario_nombre + ' · Caja #' + destino?.id
    + '. Importe en efectivo: $ ' + formatMoney(pendiente.value.importe, { fractionDigits: 2 })
    + '. Motivo: ' + pendiente.value.motivo + '. El destino se acredita automáticamente al confirmar.'
})

async function confirmar() {
  if (!pendiente.value || loading.value) return
  try {
    const saved = await transferir(pendiente.value)
    if (saved) {
      comprobante.value = saved
      pendiente.value = null
      formVersion.value += 1
    }
  } catch {
    pendiente.value = null
    // El composable expone el error de API; el formulario conserva sus datos.
  }
}
onMounted(load)
</script>

<style scoped>
.transfer-workspace { display: grid; gap: 1.5rem; }
.transfer-page-heading { display: flex; align-items: start; justify-content: space-between; gap: 1rem; }
.transfer-page-heading h1 { font-size: clamp(1.5rem, 3vw, 2rem); margin: .25rem 0 .5rem; }
.transfer-page-heading p:last-child { color: var(--color-text-secondary); }
.transfer-receipt { border: 1px solid; border-left: 4px solid #16a34a; border-radius: 1rem; padding: 1.25rem; }
.transfer-receipt p { margin-top: .5rem; }
.transfer-error { border-left: 4px solid #b42318; padding: 1rem; background: #fff4f2; color: #8f1d14; }
.transfer-error button { margin-top: .75rem; }
.transfer-empty { padding: 1rem; border: 1px dashed var(--color-border); border-radius: 1rem; }
@media (max-width: 640px) { .transfer-page-heading { flex-direction: column; } }
</style>
