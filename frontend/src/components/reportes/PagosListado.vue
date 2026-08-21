<template>
  <section class="reports-payments-card border-border bg-surface">
    <header class="reports-payments-head">
      <div class="reports-payments-title">
        <span class="reports-payments-icon">
          <ReceiptPercentIcon aria-hidden="true" />
        </span>
        <div>
          <p class="eyebrow">Detalle de operaciones</p>
          <h2>Pagos del período</h2>
          <p>Comprobantes incluidos en el reporte actual.</p>
        </div>
      </div>
      <span class="reports-payments-count">
        {{ pagos.length }} {{ pagos.length === 1 ? 'pago' : 'pagos' }}
      </span>
    </header>

    <div class="reports-payments-table-wrap">
      <table class="reports-payments-table">
        <thead>
          <tr>
            <th>Recibo</th>
            <th>Fecha</th>
            <th>Alumno</th>
            <th>Concepto</th>
            <th>Sucursal</th>
            <th>Medio</th>
            <th>Importe</th>
            <th><span class="sr-only">Acciones</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pago in pagos" :key="pago.id">
            <td>
              <span class="reports-receipt-number">
                <DocumentTextIcon aria-hidden="true" />
                {{ pago.numero_recibo || 'Sin número' }}
              </span>
            </td>
            <td class="reports-payment-date">{{ formatDate(pago.fecha) || '—' }}</td>
            <td>
              <span class="reports-student-name">
                <UserCircleIcon aria-hidden="true" />
                {{ pago.alumno_nombre || 'Sin alumno' }}
              </span>
            </td>
            <td class="reports-payment-concept">{{ pago.concepto_nombre || 'Pago a cuenta' }}</td>
            <td>
              <span class="reports-payment-branch">
                <MapPinIcon aria-hidden="true" />
                {{ pago.sucursal_nombre || 'Sin sucursal' }}
              </span>
            </td>
            <td>
              <span class="reports-payment-method">
                <component :is="paymentIcon(pago.medio)" aria-hidden="true" />
                {{ paymentLabel(pago.medio) }}
              </span>
            </td>
            <td class="reports-payment-amount">
              $ {{ formatMoney(pago.importe, { fractionDigits: 2 }) }}
            </td>
            <td>
              <button
                v-if="pago.id"
                class="reports-print-action"
                type="button"
                title="Imprimir recibo"
                aria-label="Imprimir recibo"
                :disabled="printingId === pago.id"
                @click="printRecibo(pago)"
              >
                <ArrowPathIcon v-if="printingId === pago.id" class="is-spinning" aria-hidden="true" />
                <PrinterIcon v-else aria-hidden="true" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="pagos.length" class="mobile-record-list reports-mobile-list" role="list">
        <article
          v-for="pago in pagos"
          :key="`mobile-${pago.id}`"
          class="mobile-record-card report-mobile-card"
          role="listitem"
        >
          <header class="mobile-record-head">
            <span class="mobile-record-icon info">
              <DocumentTextIcon aria-hidden="true" />
            </span>
            <span class="mobile-record-title">
              <strong>{{ pago.numero_recibo || 'Sin número' }}</strong>
              <small>{{ formatDate(pago.fecha) || 'Sin fecha' }}</small>
            </span>
            <strong class="mobile-record-amount">
              $ {{ formatMoney(pago.importe, { fractionDigits: 2 }) }}
            </strong>
          </header>

          <div class="report-mobile-student">
            <UserCircleIcon aria-hidden="true" />
            <span>
              <small>Alumno</small>
              <strong>{{ pago.alumno_nombre || 'Sin alumno' }}</strong>
            </span>
          </div>

          <dl class="mobile-record-meta">
            <div>
              <dt>Concepto</dt>
              <dd>{{ pago.concepto_nombre || 'Pago a cuenta' }}</dd>
            </div>
            <div>
              <dt>Sucursal</dt>
              <dd><MapPinIcon aria-hidden="true" />{{ pago.sucursal_nombre || 'Sin sucursal' }}</dd>
            </div>
          </dl>

          <footer class="mobile-record-footer">
            <span class="reports-payment-method">
              <component :is="paymentIcon(pago.medio)" aria-hidden="true" />
              {{ paymentLabel(pago.medio) }}
            </span>
            <button
              v-if="pago.id"
              class="mobile-record-action"
              type="button"
              :disabled="printingId === pago.id"
              @click="printRecibo(pago)"
            >
              <ArrowPathIcon v-if="printingId === pago.id" class="is-spinning" aria-hidden="true" />
              <PrinterIcon v-else aria-hidden="true" />
              <span>{{ printingId === pago.id ? 'Preparando…' : 'Imprimir recibo' }}</span>
            </button>
          </footer>
        </article>
      </div>

      <div v-if="!pagos.length" class="reports-payments-empty">
        <span><DocumentMagnifyingGlassIcon aria-hidden="true" /></span>
        <strong>No encontramos pagos</strong>
        <p>Modificá el período o los filtros para consultar otras operaciones.</p>
      </div>
    </div>

    <ReciboPrintView :recibo="reciboData" />
  </section>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import {
  ArrowPathIcon,
  BanknotesIcon,
  BuildingLibraryIcon,
  CreditCardIcon,
  DocumentMagnifyingGlassIcon,
  DocumentTextIcon,
  MapPinIcon,
  PrinterIcon,
  QuestionMarkCircleIcon,
  ReceiptPercentIcon,
  UserCircleIcon,
} from '@heroicons/vue/24/outline'
import { usePagos } from '@/composables/usePagos'
import { useToast } from '@/composables/useToast'
import { formatDate, formatMoney } from '@/lib/formatters'
import ReciboPrintView from '@/components/ui/ReciboPrintView.vue'

defineProps({
  pagos: { type: Array, required: true },
})

const { getRecibo } = usePagos()
const toast = useToast()

const reciboData = ref(null)
const printingId = ref(null)

function paymentIcon(method) {
  if (method === 'efectivo') return BanknotesIcon
  if (method === 'transferencia') return BuildingLibraryIcon
  if (method === 'mercado_pago') return CreditCardIcon
  if (method === 'tarjeta') return CreditCardIcon
  return QuestionMarkCircleIcon
}

function paymentLabel(method) {
  const labels = {
    efectivo: 'Efectivo',
    transferencia: 'Transferencia',
    mercado_pago: 'Mercado Pago',
    tarjeta: 'Tarjeta',
    otro: 'Otro',
  }
  return labels[method] || method || 'Sin medio'
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
</script>
