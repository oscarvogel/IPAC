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
          </div>
        </section>
        <footer class="modal-actions">
          <button class="secondary-button" type="button" :disabled="loading" @click="requestClose">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="loading" type="submit">
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
const cajaSucursal = computed(() => props.cajaHoy?.sucursal_nombre || props.cajaHoy?.sucursal?.nombre || 'Sin sucursal')
const cajaFecha = computed(() => props.cajaHoy?.fecha ? formatDate(props.cajaHoy.fecha) : 'Sin fecha')
const diferencia = computed(() => Number(totalContado.value || 0) - Number(props.totalEsperado || 0))
const tieneDiferencia = computed(() => Math.abs(diferencia.value) > 0.005)

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

async function submit() {
  const contado = Number(totalContado.value || 0)
  const diferencia = contado - Number(props.totalEsperado || 0)
  const confirmation = await confirmCierreCaja({
    sucursal: props.cajaHoy?.sucursal_nombre || 'Sin sucursal',
    fecha: props.cajaHoy?.fecha ? formatDate(props.cajaHoy.fecha) : 'Sin fecha',
    totalEsperado: props.totalEsperado,
    totalContado: contado,
    diferencia,
  })
  if (confirmation.isConfirmed) emit('submit', totalContado.value)
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
