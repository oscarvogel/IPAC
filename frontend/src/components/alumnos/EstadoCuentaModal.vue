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
            <span>Cuenta corriente real con cuotas, pagos, aplicaciones y saldos.</span>
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
              <span>Total cuotas</span>
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
            <article class="account-net-total">
              <span>Saldo neto</span>
              <strong :class="netBalanceClass">$ {{ formatMoney(Math.abs(Number(data.resumen.saldo_neto || 0))) }}</strong>
              <small>{{ netBalanceLabel }}</small>
            </article>
          </section>

          <section class="modal-section">
            <h3>Cuotas</h3>
            <div class="account-list">
              <div v-for="cuota in data.cuotas" :key="cuota.id" class="account-row account-row-detailed">
                <div class="account-main">
                  <strong>{{ cuota.concepto_nombre }}</strong>
                  <span>
                    {{ cuota.periodo }} ·
                    vto {{ formatDate(cuota.fecha_vencimiento) }} ·
                    <em :class="`estado-${cuota.estado}`">{{ estadoLabel(cuota.estado) }}</em>
                  </span>
                  <div class="account-breakdown">
                    <span>Importe: $ {{ formatMoney(cuota.importe) }}</span>
                    <span v-if="Number(cuota.descuento || 0) > 0">Descuento: -$ {{ formatMoney(cuota.descuento) }}</span>
                    <span v-if="Number(cuota.recargo || 0) > 0">Recargo: +$ {{ formatMoney(cuota.recargo) }}</span>
                    <span>Total: $ {{ formatMoney(cuota.total) }}</span>
                    <span>Pagado: $ {{ formatMoney(cuota.total_pagado) }}</span>
                  </div>
                </div>
                <div class="account-balance">
                  <span>Saldo</span>
                  <strong>$ {{ formatMoney(cuota.saldo) }}</strong>
                </div>
              </div>
              <p v-if="!data.cuotas.length" class="empty-state flat">
                Sin cuotas registradas.
              </p>
            </div>
          </section>

          <section class="modal-section">
            <h3>Pagos</h3>
            <div class="account-list">
              <div v-for="pago in data.pagos" :key="pago.id" class="account-row account-row-detailed payment-row">
                <div class="account-main">
                  <strong>{{ pago.concepto_nombre || 'Pago a cuenta' }}</strong>
                  <span>
                    {{ formatDate(pago.fecha) }} ·
                    {{ medioLabel(pago.medio) }} ·
                    <em v-if="pago.numero_recibo">{{ pago.numero_recibo }}</em>
                    <em v-if="pago.estado === 'anulado'" class="payment-void-badge">ANULADO</em>
                  </span>

                  <div class="account-breakdown">
                    <span>Importe: $ {{ formatMoney(pago.importe) }}</span>
                    <span>Aplicado: $ {{ formatMoney(pago.importe_aplicado) }}</span>
                    <span v-if="Number(pago.saldo_a_favor || 0) > 0">Saldo a favor: $ {{ formatMoney(pago.saldo_a_favor) }}</span>
                  </div>

                  <div v-if="pago.aplicaciones?.length" class="payment-applications">
                    <span class="payment-applications-title">Aplicaciones</span>
                    <div v-for="aplicacion in pago.aplicaciones" :key="aplicacion.id" class="payment-application-row">
                      <span>{{ cuotaAplicacionLabel(aplicacion.cuota) }}</span>
                      <strong>$ {{ formatMoney(aplicacion.importe) }}</strong>
                    </div>
                  </div>
                  <p v-else-if="Number(pago.saldo_a_favor || 0) > 0" class="payment-unapplied-note">
                    Este pago todavía no fue aplicado a cuotas.
                  </p>
                </div>

                <div class="account-row-end">
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
                  <button
                    v-if="pago.estado !== 'anulado' && auth.can('void-payments')"
                    class="void-payment-btn"
                    type="button"
                    title="Anular pago"
                    aria-label="Anular pago"
                    :disabled="cancellingId === pago.id"
                    @click="voidPayment(pago)"
                  >
                    <ArrowPathIcon v-if="cancellingId === pago.id" class="is-spinning" aria-hidden="true" />
                    <NoSymbolIcon v-else aria-hidden="true" />
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
import { ArrowPathIcon, NoSymbolIcon, PrinterIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import { usePagos } from '@/composables/usePagos'
import { useAuth } from '@/composables/useAuth'
import { useToast } from '@/composables/useToast'
import { formatMoney, formatDate } from '@/lib/formatters'
import { confirmAnularPago } from '@/lib/swal'
import ReciboPrintView from '@/components/ui/ReciboPrintView.vue'
import { vFocusTrap } from '@/directives/accessibility'

const props = defineProps({
  open: { type: Boolean, default: false },
  alumno: { type: Object, default: null },
})

const emit = defineEmits(['close'])

const { getEstadoCuenta, getRecibo, anularPago } = usePagos()
const auth = useAuth()
const toast = useToast()

const data = ref(null)
const loading = ref(false)
const reciboData = ref(null)
const printingId = ref(null)
const cancellingId = ref(null)

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

async function voidPayment(pago) {
  if (!pago.id || cancellingId.value) return
  const confirmation = await confirmAnularPago({
    recibo: pago.numero_recibo,
    alumno: `${props.alumno?.apellido || ''}, ${props.alumno?.nombre || ''}`,
    importe: pago.importe,
  })
  if (!confirmation.isConfirmed) return
  cancellingId.value = pago.id
  try {
    await anularPago(pago.id, confirmation.value)
    await loadAccount()
    toast.success('Pago anulado y caja ajustada.')
  } catch (err) {
    toast.error(err.message || 'No se pudo anular el pago.')
  } finally {
    cancellingId.value = null
  }
}

const paidTotal = computed(() => {
  if (!data.value?.pagos) return 0
  return data.value.pagos
    .filter((pago) => pago.estado !== 'anulado')
    .reduce((sum, pago) => sum + Number(pago.importe || 0), 0)
})

const cuotasById = computed(() => {
  const entries = (data.value?.cuotas || []).map((cuota) => [Number(cuota.id), cuota])
  return new Map(entries)
})

const netBalanceClass = computed(() => {
  const value = Number(data.value?.resumen?.saldo_neto || 0)
  if (value > 0) return 'balance-debt'
  if (value < 0) return 'balance-credit'
  return 'balance-zero'
})

const netBalanceLabel = computed(() => {
  const value = Number(data.value?.resumen?.saldo_neto || 0)
  if (value > 0) return 'Deuda neta del alumno'
  if (value < 0) return 'Crédito neto a favor del alumno'
  return 'Cuenta al día'
})

function estadoLabel(estado) {
  const labels = {
    pendiente: 'Pendiente',
    parcial: 'Parcial',
    pagada: 'Pagada',
    anulada: 'Anulada',
  }
  return labels[estado] || estado
}

function medioLabel(medio) {
  const labels = {
    efectivo: 'Efectivo',
    transferencia: 'Transferencia',
    mercado_pago: 'Mercado Pago',
    tarjeta: 'Tarjeta',
    otro: 'Otro',
  }
  return labels[medio] || medio
}

function cuotaAplicacionLabel(cuotaId) {
  const cuota = cuotasById.value.get(Number(cuotaId))
  if (!cuota) return `Cuota #${cuotaId}`
  return `${cuota.concepto_nombre} · ${cuota.periodo}`
}

watch(
  () => [props.open, props.alumno?.id],
  async ([isOpen, id]) => {
    if (!isOpen || !id) {
      data.value = null
      return
    }
    await loadAccount(id)
  },
  { immediate: true },
)

async function loadAccount(id = props.alumno?.id) {
  if (!id) return
  loading.value = true
  try {
    data.value = await getEstadoCuenta(id)
  } catch (err) {
    toast.error(err.message || 'No se pudo cargar el estado de cuenta.')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.estado-pendiente { color: var(--warning); }
.estado-parcial { color: var(--primary); }
.estado-pagada { color: var(--success); }
.estado-anulada { color: var(--text-muted); text-decoration: line-through; }

.payment-void-badge {
  margin-left: 6px;
  color: var(--danger);
  font-weight: 800;
  text-decoration: none;
}

.void-payment-btn {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--danger) 35%, var(--border));
  border-radius: 9px;
  color: var(--danger);
  background: color-mix(in srgb, var(--danger) 6%, var(--surface));
}

.void-payment-btn svg { width: 18px; height: 18px; }

.account-net-total {
  min-width: 190px;
}

.account-net-total small {
  display: block;
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 12px;
}

.balance-debt { color: var(--danger); }
.balance-credit { color: var(--success); }
.balance-zero { color: var(--text-primary); }

.account-row-detailed {
  align-items: flex-start;
}

.account-main {
  min-width: 0;
  flex: 1;
}

.account-breakdown {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  margin-top: 7px;
  color: var(--text-secondary);
  font-size: 12px;
}

.account-balance {
  display: grid;
  justify-items: end;
  gap: 2px;
  min-width: 110px;
}

.account-balance span {
  color: var(--text-secondary);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.payment-applications {
  display: grid;
  gap: 5px;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed var(--line);
}

.payment-applications-title {
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.payment-application-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  font-size: 12px;
}

.payment-unapplied-note {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 12px;
}

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

@media (max-width: 700px) {
  .account-row-detailed {
    display: grid;
    gap: 10px;
  }

  .account-balance {
    justify-items: start;
  }

  .payment-row .account-row-end {
    justify-content: flex-end;
  }
}
</style>
