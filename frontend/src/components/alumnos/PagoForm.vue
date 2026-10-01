<template>
  <Teleport to="body">
    <AppModalTransition :open="open">
      <div class="modal-backdrop" @click.self="requestClose">
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
            <h2 id="pago-form-title">{{ savedPago ? 'Pago registrado' : 'Registrar pago' }}</h2>
            <span v-if="alumno">{{ alumno.apellido }}, {{ alumno.nombre }}</span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar formulario" @click="requestClose">
            <XMarkIcon aria-hidden="true" />
          </button>
        </header>

        <section v-if="savedPago" ref="confirmationSection" class="modal-section payment-confirmation" aria-live="polite">
          <template v-if="!showReceipt">
            <p>El pago quedó registrado. Ya podés consultar su recibo.</p>
            <dl><div><dt>Alumno</dt><dd>{{ savedPago.alumno_nombre || savedAlumno }}</dd></div><div><dt>Importe</dt><dd>$ {{ formatMoney(savedPago.importe) }}</dd></div><div><dt>Medio</dt><dd>{{ medioLabel(savedPago.medio) }}</dd></div><div><dt>Recibo</dt><dd>{{ savedPago.numero_recibo || 'Número no informado' }}</dd></div></dl>
            <div class="modal-actions"><button class="primary-button" type="button" :disabled="readingReceipt" @click="readReceipt(false)">Ver recibo</button><button class="secondary-button" type="button" :disabled="readingReceipt" @click="readReceipt(true)">Imprimir</button><button class="secondary-button" type="button" @click="requestClose">Finalizar</button></div>
          </template>
          <template v-else><button type="button" class="secondary-button" @click="showReceipt = false">Volver a la confirmación</button><ReciboVista v-if="receipt" ref="receiptView" :recibo="receipt" /></template>
          <p v-if="receiptError" role="alert">{{ receiptError }} <button class="secondary-button" type="button" @click="readReceipt(false)">Reintentar recibo</button></p>
          <p v-if="refreshError" role="alert">El pago está registrado, pero no se pudo actualizar la lista. {{ refreshError }} <button class="secondary-button" type="button" :disabled="refreshLoading" @click="$emit('retry-refresh')">Reintentar actualización</button></p>
        </section>
        <section v-else class="modal-section">
          <AyudaContextual guia="pagos" :modo="form.modo" />
          <p v-if="cuotasError" role="alert">{{ cuotasError }} <button type="button" class="secondary-button" @click="loadCuotas">Reintentar cuotas</button></p>
          <div class="payment-debt-summary" aria-live="polite">
            <span>Deuda pendiente</span>
            <strong>$ {{ formatMoney(totalPendingDebt) }}</strong>
            <small>{{ pendingCuotas.length }} {{ pendingCuotas.length === 1 ? 'cuota pendiente' : 'cuotas pendientes' }}</small>
          </div>

          <div class="modal-grid">
            <fieldset class="payment-application-options" :disabled="loadingCuotas || Boolean(cuotasError)">
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

        <footer v-if="!savedPago" class="modal-actions">
          <button class="secondary-button" type="button" :disabled="saving" @click="requestClose">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="saving || loadingCuotas || confirming || Boolean(cuotasError)" type="submit">
            <AppButtonContent :loading="saving" label="Guardar pago" loading-label="Guardando…" />
          </button>
        </footer>
      </form>
      </div>
    </AppModalTransition>
  </Teleport>
</template>

<style scoped>
.payment-confirmation dl{display:grid;gap:.8rem}.payment-confirmation dl>div{display:grid;grid-template-columns:6rem 1fr;gap:.6rem}.payment-confirmation dt{color:var(--text-secondary)}.payment-confirmation dd{margin:0;font-weight:700;overflow-wrap:anywhere}.payment-confirmation [role=alert]{color:var(--danger)}.payment-confirmation button{min-height:44px;white-space:normal}
.field-help {
  display: block;
  margin-top: 5px;
  color: var(--text-secondary);
  font-size: 12px;
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
  font-size: 12px;
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
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import { usePagos } from '@/composables/usePagos'
import AppModalTransition from '@/components/ui/AppModalTransition.vue'
import { useToast } from '@/composables/useToast'
import { confirmSaldoAFavor } from '@/lib/swal'
import { formatDate, formatMoney } from '@/lib/formatters'
import AppButtonContent from '@/components/ui/AppButtonContent.vue'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'
import ReciboVista from '@/components/ui/ReciboVista.vue'
import AyudaContextual from '@/components/ui/AyudaContextual.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  alumno: { type: Object, default: null },
  conceptos: { type: Array, default: () => [] },
  refreshError: { type: String, default: '' },
  refreshLoading: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'saved', 'retry-refresh'])

const { createPago, getRecibo, getEstadoCuenta } = usePagos()
const toast = useToast()

const form = reactive({
  modo: 'automatico',
  cuotas: [],
  importe: '',
  medio: 'efectivo',
  observacion: '',
})

const saving = ref(false)
const confirming = ref(false)
const savedPago = ref(null), savedAlumno = ref(''), receipt = ref(null), receiptError = ref(''), readingReceipt = ref(false), showReceipt = ref(false), receiptView = ref(null)
const confirmationSection = ref(null)
watch(showReceipt, async () => { await nextTick(); confirmationSection.value?.querySelector('button')?.focus() })
let receiptRevision = 0
function medioLabel(value) { return { efectivo: 'Efectivo', transferencia: 'Transferencia', mercado_pago: 'Mercado Pago', tarjeta: 'Tarjeta', otro: 'Otro' }[value] || value }
async function readReceipt(print) {
  if (readingReceipt.value || !savedPago.value) return
  const current = receiptRevision
  readingReceipt.value = true; receiptError.value = ''
  try {
    const data = await getRecibo(savedPago.value.id)
    if (current !== receiptRevision) return
    receipt.value = data; showReceipt.value = true
    if (print) { await nextTick(); await receiptView.value?.imprimir() }
  } catch (err) { if (current === receiptRevision) receiptError.value = err.message || 'No se pudo cargar el recibo.' }
  finally { if (current === receiptRevision) readingReceipt.value = false }
}
const loadingCuotas = ref(false)
const cuotas = ref([])
const cuotasError = ref('')
let cuotasRevision = 0

async function loadCuotas() {
  const id = props.alumno?.id
  if (!id || savedPago.value) return
  const current = ++cuotasRevision
  loadingCuotas.value = true; cuotasError.value = ''
  try {
    const estadoCuenta = await getEstadoCuenta(id)
    if (current !== cuotasRevision) return
    cuotas.value = estadoCuenta.cuotas || []
    form.modo = pendingCuotas.value.length ? 'automatico' : 'cuenta'
  } catch (err) { if (current === cuotasRevision) cuotasError.value = err.message || 'No se pudieron cargar las cuotas pendientes.' }
  finally { if (current === cuotasRevision) loadingCuotas.value = false }
}

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
    if (!isOpen) { receiptRevision++; cuotasRevision++; savedPago.value = null; receipt.value = null; return }
    if (savedPago.value) return
    showReceipt.value = false; receiptError.value = ''; readingReceipt.value = false
    form.modo = 'automatico'
    form.cuotas = []
    form.importe = ''
    form.medio = 'efectivo'
    form.observacion = ''
    cuotas.value = []
    await loadCuotas()
  },
  { immediate: true },
)

async function handleSubmit() {
  if (!props.alumno || saving.value || confirming.value || savedPago.value || loadingCuotas.value || cuotasError.value) return
  const importe = Number(form.importe)
  if (form.modo === 'manual' && !form.cuotas.length) {
    toast.error('Seleccioná al menos una cuota para aplicar el pago.')
    return
  }
  if (form.modo !== 'cuenta' && importe > targetDebt.value) {
    confirming.value = true
    const confirmation = await confirmSaldoAFavor({
      importe,
      saldo: targetDebt.value,
      importeAplicado: targetDebt.value,
      saldoFavor: importe - targetDebt.value,
    })
    confirming.value = false
    if (!confirmation.isConfirmed) return
  }
  saving.value = true
  try {
    savedAlumno.value = `${props.alumno.apellido}, ${props.alumno.nombre}`
    savedPago.value = await createPago({
      alumno: props.alumno.id,
      cuotas: form.modo === 'manual' ? form.cuotas : [],
      aplicacion_automatica: form.modo === 'automatico',
      importe: form.importe,
      medio: form.medio,
      observacion: form.observacion,
    })
    toast.success('Pago registrado')
    emit('saved', savedPago.value)
    await nextTick()
    confirmationSection.value?.querySelector('button')?.focus()
  } catch (err) {
    toast.error(err.message || 'No se pudo registrar el pago.')
  } finally {
    saving.value = false
  }
}
</script>
