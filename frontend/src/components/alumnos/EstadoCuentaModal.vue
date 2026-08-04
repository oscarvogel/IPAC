<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="requestClose">
      <section
        v-focus-trap="{ close: requestClose, busy: Boolean(printingId) }"
        class="modal-card account-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="estado-cuenta-title"
        :aria-busy="loading"
      >
        <header class="modal-head">
          <div>
            <p class="eyebrow">Estado de cuenta</p>
            <h2 id="estado-cuenta-title">{{ alumno?.nombre }} {{ alumno?.apellido }}</h2>
            <span>Resumen de cuotas, pagos y saldo a favor.</span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar estado de cuenta" @click="requestClose">
            <XMarkIcon aria-hidden="true" />
          </button>
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
                <div class="account-row-end">
                  <strong>$ {{ formatMoney(pago.importe) }}</strong>
                  <button
                    v-if="pago.id"
                    class="print-recibo-btn"
                    type="button"
                    title="Imprimir recibo"
                    aria-label="Imprimir recibo"
                    :disabled="printingId === pago.id"
                    @click="printRecibo(pago)"
                  >
                    <ArrowPathIcon v-if="printingId === pago.id" class="is-spinning" aria-hidden="true" />
                    <PrinterIcon v-else aria-hidden="true" />
                  </button>
                </div>
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

    <ReciboPrintView :recibo="reciboData" />
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { ArrowPathIcon, PrinterIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import { usePagos } from '@/composables/usePagos'
import { useToast } from '@/composables/useToast'
import { formatMoney, formatDate } from '@/lib/formatters'
import ReciboPrintView from '@/components/ui/ReciboPrintView.vue'
import { vFocusTrap } from '@/directives/accessibility'

const props = defineProps({
  open: { type: Boolean, default: false },
  alumno: { type: Object, default: null },
})

const emit = defineEmits(['close'])

const { getEstadoCuenta, getRecibo } = usePagos()
const toast = useToast()

const data = ref(null)
const loading = ref(false)
const reciboData = ref(null)
const printingId = ref(null)

function requestClose() {
  if (!printingId.value) emit('close')
}

async function printRecibo(pago) {
  if (!pago.id || printingId.value) return
  printingId.value = pago.id
  try {
    reciboData.value = await getRecibo(pago.id)
    await nextTick()
    window.print()
  } catch (err) {
    toast.error(err.message || 'No se pudo preparar el recibo para imprimir.')
  } finally {
    printingId.value = null
  }
}

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

.account-row-end {
  display: flex;
  align-items: center;
  gap: 8px;
}

.print-recibo-btn {
  width: 32px;
  height: 32px;
  padding: 7px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--surface);
  font-size: 13px;
  line-height: 1;
  cursor: pointer;
}

.print-recibo-btn svg {
  width: 16px;
  height: 16px;
}

.print-recibo-btn:disabled {
  opacity: 0.5;
}
</style>
