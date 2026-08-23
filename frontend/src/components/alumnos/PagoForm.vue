<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="requestClose">
      <form
        v-focus-trap="{ close: requestClose, busy: saving }"
        v-form-validation
        class="modal-card compact-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="pago-form-title"
        :aria-busy="saving"
        @submit.prevent="handleSubmit"
      >
        <header class="modal-head">
          <div>
            <p class="eyebrow">Cobranza</p>
            <h2 id="pago-form-title">Registrar pago</h2>
            <span v-if="alumno">{{ alumno.apellido }}, {{ alumno.nombre }}</span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar formulario" @click="requestClose">
            <XMarkIcon aria-hidden="true" />
          </button>
        </header>

        <section class="modal-section">
          <div class="payment-debt-summary" aria-live="polite">
            <span>Deuda pendiente</span>
            <strong>$ {{ formatMoney(totalPendingDebt) }}</strong>
            <small>{{ pendingCuotas.length }} {{ pendingCuotas.length === 1 ? 'cuota pendiente' : 'cuotas pendientes' }}</small>
          </div>

          <div class="modal-grid">
            <fieldset class="payment-application-options" :disabled="loadingCuotas">
              <legend>Aplicar pago</legend>
              <label>
                <input v-model="form.modo" type="radio" value="automatico" />
                <span><strong>Automáticamente</strong><small>Se aplicará a las cuotas más antiguas primero.</small></span>
              </label>
              <label>
                <input v-model="form.modo" type="radio" value="manual" />
                <span><strong>Elegir cuotas</strong><small>Seleccioná una o varias cuotas concretas.</small></span>
              </label>
              <label>
                <input v-model="form.modo" type="radio" value="cuenta" />
                <span><strong>Pago a cuenta — queda como saldo a favor</strong><small>No se aplicará a ninguna cuota.</small></span>
              </label>
            </fieldset>

            <div v-if="form.modo === 'manual'" class="payment-fee-selection">
              <span class="field-label">Cuotas seleccionadas</span>
              <label v-for="cuota in pendingCuotas" :key="cuota.id">
                <input v-model="form.cuotas" type="checkbox" :value="cuota.id" />
                <span>
                  <strong>{{ cuota.concepto_nombre }} · {{ cuota.periodo }}</strong>
                  <small>Vence {{ formatDate(cuota.fecha_vencimiento) }} · saldo $ {{ formatMoney(cuota.saldo) }}</small>
                </span>
              </label>
              <p v-if="!pendingCuotas.length" class="field-help">El alumno no tiene cuotas pendientes.</p>
            </div>
            <label>Importe<input v-model="form.importe" type="number" min="0.01" step="0.01" required /></label>
            <label>
              Medio
              <select v-model="form.medio">
                <option value="efectivo">Efectivo</option>
                <option value="transferencia">Transferencia</option>
                <option value="mercado_pago">Mercado Pago</option>
                <option value="tarjeta">Tarjeta</option>
                <option value="otro">Otro</option>
              </select>
            </label>
            <label>Observacion<input v-model="form.observacion" /></label>
          </div>
        </section>

        <footer class="modal-actions">
          <button class="secondary-button" type="button" :disabled="saving" @click="requestClose">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="saving" type="submit">
            <AppButtonContent :loading="saving" label="Guardar pago" loading-label="Guardando…" />
          </button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<style scoped>
.field-help {
  display: block;
  margin-top: 5px;
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 1.35;
}

.payment-debt-summary {
  margin-bottom: 16px;
  padding: 12px 14px;
  display: grid;
  gap: 3px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--background);
}

.payment-debt-summary > span,
.field-label {
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.payment-debt-summary strong { font-size: 22px; }
.payment-debt-summary small { color: var(--text-secondary); }

.payment-application-options,
.payment-fee-selection {
  grid-column: 1 / -1;
  display: grid;
  gap: 8px;
  border: 0;
  padding: 0;
}

.payment-application-options legend {
  margin-bottom: 7px;
  font-weight: 700;
}

.payment-application-options label,
.payment-fee-selection label {
  padding: 10px 12px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  border: 1px solid var(--border);
  border-radius: 9px;
  background: var(--surface);
}

.payment-application-options input,
.payment-fee-selection input {
  width: auto;
  margin-top: 3px;
}

.payment-application-options label > span,
.payment-fee-selection label > span {
  display: grid;
  gap: 2px;
}

.payment-application-options small,
.payment-fee-selection small {
  color: var(--text-secondary);
  line-height: 1.35;
}

.payment-fee-selection {
  max-height: 230px;
  overflow-y: auto;
}
</style>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import { usePagos } from '@/composables/usePagos'
import { useToast } from '@/composables/useToast'
import { confirmSaldoAFavor } from '@/lib/swal'
import { formatDate, formatMoney } from '@/lib/formatters'
import AppButtonContent from '@/components/ui/AppButtonContent.vue'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'

const props = defineProps({
  open: { type: Boolean, default: false },
  alumno: { type: Object, default: null },
  conceptos: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'saved'])

const { createPago, loadPagos, getEstadoCuenta } = usePagos()
const toast = useToast()

const form = reactive({
  modo: 'automatico',
  cuotas: [],
  importe: '',
  medio: 'efectivo',
  observacion: '',
})

const saving = ref(false)
const loadingCuotas = ref(false)
const cuotas = ref([])

function requestClose() {
  if (!saving.value) emit('close')
}

const pendingCuotas = computed(() => cuotas.value.filter((cuota) => cuota.estado !== 'anulada' && Number(cuota.saldo) > 0))
const selectedCuotas = computed(() => pendingCuotas.value.filter((cuota) => form.cuotas.map(String).includes(String(cuota.id))))
const totalPendingDebt = computed(() => pendingCuotas.value.reduce((sum, cuota) => sum + Number(cuota.saldo || 0), 0))
const targetDebt = computed(() => {
  if (form.modo === 'cuenta') return 0
  const target = form.modo === 'manual' ? selectedCuotas.value : pendingCuotas.value
  return target.reduce((sum, cuota) => sum + Number(cuota.saldo || 0), 0)
})

watch(
  () => [props.open, props.alumno?.id],
  async ([isOpen]) => {
    if (!isOpen) return
    form.modo = 'automatico'
    form.cuotas = []
    form.importe = ''
    form.medio = 'efectivo'
    form.observacion = ''
    cuotas.value = []
    if (!props.alumno) return
    loadingCuotas.value = true
    try {
      const estadoCuenta = await getEstadoCuenta(props.alumno.id)
      cuotas.value = estadoCuenta.cuotas || []
      form.modo = cuotas.value.some((cuota) => cuota.estado !== 'anulada' && Number(cuota.saldo) > 0)
        ? 'automatico'
        : 'cuenta'
    } catch (err) {
      toast.error(err.message || 'No se pudieron cargar las cuotas pendientes.')
    } finally {
      loadingCuotas.value = false
    }
  },
  { immediate: true },
)

async function handleSubmit() {
  if (!props.alumno) return
  const importe = Number(form.importe)
  if (form.modo === 'manual' && !form.cuotas.length) {
    toast.error('Seleccioná al menos una cuota para aplicar el pago.')
    return
  }
  if (form.modo !== 'cuenta' && importe > targetDebt.value) {
    const confirmation = await confirmSaldoAFavor({
      importe,
      saldo: targetDebt.value,
      importeAplicado: targetDebt.value,
      saldoFavor: importe - targetDebt.value,
    })
    if (!confirmation.isConfirmed) return
  }
  saving.value = true
  try {
    await createPago({
      alumno: props.alumno.id,
      cuotas: form.modo === 'manual' ? form.cuotas : [],
      aplicacion_automatica: form.modo === 'automatico',
      importe: form.importe,
      medio: form.medio,
      observacion: form.observacion,
    })
    await loadPagos()
    toast.success('Pago registrado')
    emit('saved')
    emit('close')
  } catch (err) {
    toast.error(err.message || 'No se pudo registrar el pago.')
  } finally {
    saving.value = false
  }
}
</script>
