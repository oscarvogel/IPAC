<template>
  <div class="panel table-card">
    <div class="panel-head">
      <div>
        <h2>Pagos en el periodo</h2>
        <p>{{ pagos.length }} pagos visibles</p>
      </div>
    </div>
    <table>
      <thead>
        <tr>
          <th>Recibo</th>
          <th>Fecha</th>
          <th>Alumno</th>
          <th>Concepto</th>
          <th>Sucursal</th>
          <th>Medio</th>
          <th>Importe</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="pago in pagos" :key="pago.id">
          <td>{{ pago.numero_recibo || '—' }}</td>
          <td>{{ formatDate(pago.fecha) }}</td>
          <td>{{ pago.alumno_nombre || '—' }}</td>
          <td>{{ pago.concepto_nombre || 'Pago a cuenta' }}</td>
          <td>{{ pago.sucursal_nombre || '—' }}</td>
          <td><span class="table-badge">{{ pago.medio }}</span></td>
          <td>$ {{ formatMoney(pago.importe, { fractionDigits: 2 }) }}</td>
          <td>
            <button
              v-if="pago.id"
              class="table-icon-button"
              type="button"
              title="Imprimir recibo"
              :disabled="printingId === pago.id"
              @click="printRecibo(pago)"
            >
              {{ printingId === pago.id ? '...' : '🖨' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!pagos.length" class="empty-state flat">
      No hay pagos para el filtro actual.
    </p>

    <ReciboPrintView :recibo="reciboData" />
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { usePagos } from '@/composables/usePagos'
import { formatDate, formatMoney } from '@/lib/formatters'
import ReciboPrintView from '@/components/ui/ReciboPrintView.vue'

defineProps({
  pagos: { type: Array, required: true },
})

const { getRecibo } = usePagos()

const reciboData = ref(null)
const printingId = ref(null)

async function printRecibo(pago) {
  if (!pago.id || printingId.value) return
  printingId.value = pago.id
  try {
    reciboData.value = await getRecibo(pago.id)
    await nextTick()
    window.print()
  } catch {
    // Si falla, el recibo queda vacio y no se imprime nada
  } finally {
    printingId.value = null
  }
}
</script>

<style scoped>
.table-icon-button {
  padding: 4px 8px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  font-size: 14px;
  line-height: 1;
}

.table-icon-button:disabled {
  opacity: 0.5;
}
</style>
