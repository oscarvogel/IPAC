<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="$emit('close')">
      <section class="modal-card account-modal">
        <header class="modal-head">
          <div>
            <p class="eyebrow">Estado de cuenta</p>
            <h2>{{ alumno?.nombre }} {{ alumno?.apellido }}</h2>
            <span>Resumen de cuotas, pagos y saldo a favor.</span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar" @click="$emit('close')">×</button>
        </header>

        <section v-if="loading" class="modal-section">
          <p class="empty-state flat">Cargando estado de cuenta...</p>
        </section>

        <template v-else-if="data">
          <section class="account-totals">
            <article>
              <span>Cuotas</span>
              <strong>$ {{ formatMoney(data.resumen.total_cuotas) }}</strong>
            </article>
            <article>
              <span>Pagado</span>
              <strong>$ {{ formatMoney(paidTotal) }}</strong>
            </article>
            <article>
              <span>Saldo pendiente</span>
              <strong>$ {{ formatMoney(data.resumen.saldo_pendiente) }}</strong>
            </article>
            <article>
              <span>Saldo a favor</span>
              <strong>$ {{ formatMoney(data.resumen.saldo_a_favor) }}</strong>
            </article>
          </section>

          <section class="modal-section">
            <h3>Cuotas</h3>
            <div class="account-list">
              <div v-for="cuota in data.cuotas" :key="cuota.id" class="account-row">
                <div>
                  <strong>{{ cuota.concepto_nombre }}</strong>
                  <span>
                    {{ cuota.periodo }} ·
                    vto {{ formatDate(cuota.fecha_vencimiento) }} ·
                    <em :class="`estado-${cuota.estado}`">{{ cuota.estado }}</em>
                  </span>
                </div>
                <strong>$ {{ formatMoney(cuota.saldo) }}</strong>
              </div>
              <p v-if="!data.cuotas.length" class="empty-state flat">
                Sin cuotas registradas.
              </p>
            </div>
          </section>

          <section class="modal-section">
            <h3>Pagos</h3>
            <div class="account-list">
              <div v-for="pago in data.pagos" :key="pago.id" class="account-row">
                <div>
                  <strong>{{ pago.concepto_nombre || 'Pago a cuenta' }}</strong>
                  <span>
                    {{ formatDate(pago.fecha) }} ·
                    {{ pago.medio }} ·
                    <em v-if="pago.numero_recibo">{{ pago.numero_recibo }}</em>
                  </span>
                </div>
                <strong>$ {{ formatMoney(pago.importe) }}</strong>
              </div>
              <p v-if="!data.pagos.length" class="empty-state flat">
                Sin pagos registrados.
              </p>
            </div>
          </section>
        </template>

        <section v-else class="modal-section">
          <p class="empty-state flat">No se pudo cargar el estado de cuenta.</p>
        </section>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { usePagos } from '@/composables/usePagos'
import { useToast } from '@/composables/useToast'
import { formatMoney, formatDate } from '@/lib/formatters'

const props = defineProps({
  open: { type: Boolean, default: false },
  alumno: { type: Object, default: null },
})

const emit = defineEmits(['close'])

const { getEstadoCuenta } = usePagos()
const toast = useToast()

const data = ref(null)
const loading = ref(false)

const paidTotal = computed(() => {
  if (!data.value?.pagos) return 0
  return data.value.pagos.reduce((sum, p) => sum + Number(p.importe || 0), 0)
})

watch(
  () => [props.open, props.alumno?.id],
  async ([isOpen, id]) => {
    if (!isOpen || !id) {
      data.value = null
      return
    }
    loading.value = true
    data.value = null
    try {
      data.value = await getEstadoCuenta(id)
    } catch (err) {
      toast.error(err.message || 'No se pudo cargar el estado de cuenta.')
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)
</script>

<style scoped>
.estado-pendiente { color: #b45309; }
.estado-parcial { color: #1d4ed8; }
.estado-pagada { color: #047857; }
.estado-anulada { color: #6b7280; text-decoration: line-through; }
</style>
