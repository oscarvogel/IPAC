<template>
  <Teleport to="body">
    <div class="modal-backdrop" @click.self="requestClose">
      <form
        v-focus-trap="{ close: requestClose, busy: loading }"
        v-form-validation
        class="modal-card compact-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cerrar-caja-title"
        :aria-busy="loading"
        @submit.prevent="submit"
      >
        <header class="modal-head">
          <div>
            <p class="eyebrow">Cierre de caja</p>
            <h2 id="cerrar-caja-title">Cerrar caja del día</h2>
            <span>Total esperado: $ {{ formatMoney(totalEsperado) }}</span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar formulario" @click="requestClose">
            <XMarkIcon aria-hidden="true" />
          </button>
        </header>
        <section class="modal-section">
          <dl class="cash-close-summary" aria-live="polite">
            <div>
              <dt>Sucursal</dt>
              <dd>{{ cajaSucursal }}</dd>
            </div>
            <div>
              <dt>Fecha</dt>
              <dd>{{ cajaFecha }}</dd>
            </div>
            <div>
              <dt>Total esperado</dt>
              <dd>$ {{ formatMoney(totalEsperado) }}</dd>
            </div>
            <div>
              <dt>Total contado</dt>
              <dd>$ {{ formatMoney(totalContado) }}</dd>
            </div>
            <div :class="{ 'cash-close-difference-warning': tieneDiferencia }">
              <dt>Diferencia</dt>
              <dd>$ {{ formatMoney(diferencia) }}</dd>
            </div>
          </dl>
          <p v-if="tieneDiferencia" class="cash-close-warning" role="status">
            Hay una diferencia entre el total esperado y el total contado. Se registrará en el cierre.
          </p>
          <div class="modal-grid">
            <label>Total contado<input v-model.number="totalContado" type="number" step="0.01" required /></label>
            <label>
              Efectivo a retirar
              <input v-model.number="importeRetirado" type="number" min="0" step="0.01" required />
              <small>Importe que sale físicamente de la sucursal al cerrar.</small>
            </label>
            <label>
              Dejar para próxima apertura
              <input v-model.number="saldoArrastrable" type="number" min="0" :max="totalContado" step="0.01" required />
              <small>Quedará disponible como saldo inicial de la próxima caja de esta sucursal.</small>
            </label>
          </div>
          <p v-if="!distribucionValida" class="cash-close-warning" role="alert">
            El efectivo retirado más el importe para la próxima apertura debe coincidir con el total contado.
          </p>
        </section>
        <footer class="modal-actions">
          <button class="secondary-button" type="button" :disabled="loading" @click="requestClose">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="loading || !distribucionValida" type="submit">
            <AppButtonContent :loading="loading" label="Cerrar caja" loading-label="Cerrando" />
          </button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import { formatDate, formatMoney } from '@/lib/formatters'
import { confirmCierreCaja } from '@/lib/swal'
import AppButtonContent from '@/components/ui/AppButtonContent.vue'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'

const props = defineProps({
  totalEsperado: { type: Number, default: 0 },
  cajaHoy: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'submit'])
const totalContado = ref(Number(props.totalEsperado || 0).toFixed(2))
const importeRetirado = ref(Number(props.totalEsperado || 0).toFixed(2))
const saldoArrastrable = ref('0.00')
const cajaSucursal = computed(() => props.cajaHoy?.sucursal_nombre || props.cajaHoy?.sucursal?.nombre || 'Sin sucursal')
const cajaFecha = computed(() => props.cajaHoy?.fecha ? formatDate(props.cajaHoy.fecha) : 'Sin fecha')
const diferencia = computed(() => Number(totalContado.value || 0) - Number(props.totalEsperado || 0))
const tieneDiferencia = computed(() => Math.abs(diferencia.value) > 0.005)
const distribucionValida = computed(() => {
  const contado = Number(totalContado.value || 0)
  const retirado = Number(importeRetirado.value || 0)
  const arrastrable = Number(saldoArrastrable.value || 0)
  return contado >= 0
    && retirado >= 0
    && arrastrable >= 0
    && arrastrable <= contado
    && Math.abs(retirado + arrastrable - contado) < 0.005
})

function requestClose() {
  if (!props.loading) emit('close')
}

watch(
  () => props.totalEsperado,
  (next) => {
    if (totalContado.value === '' || totalContado.value == null) {
      totalContado.value = Number(next || 0).toFixed(2)
    }
  },
)

watch([totalContado, saldoArrastrable], ([contado, arrastrable]) => {
  importeRetirado.value = Math.max(Number(contado || 0) - Number(arrastrable || 0), 0).toFixed(2)
})

async function submit() {
  const contado = Number(totalContado.value || 0)
  const diferencia = contado - Number(props.totalEsperado || 0)
  const confirmation = await confirmCierreCaja({
    sucursal: props.cajaHoy?.sucursal_nombre || 'Sin sucursal',
    fecha: props.cajaHoy?.fecha ? formatDate(props.cajaHoy.fecha) : 'Sin fecha',
    totalEsperado: props.totalEsperado,
    totalContado: contado,
    diferencia,
    importeRetirado: Number(importeRetirado.value || 0),
    saldoArrastrable: Number(saldoArrastrable.value || 0),
  })
  if (confirmation.isConfirmed) {
    emit('submit', {
      total_contado: totalContado.value,
      importe_retirado: importeRetirado.value,
      saldo_arrastrable: saldoArrastrable.value,
    })
  }
}
</script>

<style scoped>
.cash-close-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: .65rem 1rem;
  margin: 0 0 1rem;
}

.cash-close-summary div {
  display: flex;
  justify-content: space-between;
  gap: .75rem;
  border-bottom: 1px solid var(--border, #e2e8f0);
  padding-bottom: .45rem;
}

.cash-close-summary dt {
  color: var(--text-secondary, #64748b);
}

.cash-close-summary dd {
  margin: 0;
  font-weight: 700;
  text-align: right;
}

.cash-close-difference-warning {
  color: #9f1239;
}

.cash-close-warning {
  margin: 0 0 1rem;
  border-radius: .65rem;
  padding: .7rem .8rem;
  color: #92400e;
  background: #fffbeb;
  font-size: .85rem;
}

@media (max-width: 520px) {
  .cash-close-summary {
    grid-template-columns: 1fr;
  }
}
</style>
