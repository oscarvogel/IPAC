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
          <div class="modal-grid">
            <label>
              Aplicar a
              <select v-model="form.cuota" :disabled="loadingCuotas">
                <option value="">Pago a cuenta — queda como saldo a favor</option>
                <option v-for="cuota in pendingCuotas" :key="cuota.id" :value="cuota.id">
                  {{ cuota.concepto_nombre }} · {{ cuota.periodo }} · saldo $ {{ cuota.saldo }}
                </option>
              </select>
              <small class="field-help">Elegí una cuota para imputar el pago o dejalo a cuenta si todavía no querés asociarlo a una cuota.</small>
            </label>
            <label>Importe<input v-model="form.importe" type="number" min="0" step="0.01" required /></label>
            <label>
              Medio
              <select v-model="form.medio">
                <option value="efectivo">Efectivo</option>
                <option value="transferencia">Transferencia</option>
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
</style>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import { usePagos } from '@/composables/usePagos'
import { useToast } from '@/composables/useToast'
import { confirmSaldoAFavor } from '@/lib/swal'
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
  cuota: '',
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
const selectedCuota = computed(() => pendingCuotas.value.find((cuota) => String(cuota.id) === String(form.cuota)) || null)

watch(
  () => [props.open, props.alumno?.id],
  async ([isOpen]) => {
    if (!isOpen) return
    form.cuota = ''
    form.importe = ''
    form.medio = 'efectivo'
    form.observacion = ''
    cuotas.value = []
    if (!props.alumno) return
    loadingCuotas.value = true
    try {
      const estadoCuenta = await getEstadoCuenta(props.alumno.id)
      cuotas.value = estadoCuenta.cuotas || []
    } catch (err) {
      toast.error(err.message || 'No se pudieron cargar las cuotas pendientes.')
    } finally {
      loadingCuotas.value = false
    }
  },
  { immediate: true },
)

watch(
  () => form.cuota,
  (cuotaId) => {
    if (!cuotaId) return
    const cuota = pendingCuotas.value.find((item) => String(item.id) === String(cuotaId))
    if (cuota) form.importe = cuota.saldo
  },
)

async function handleSubmit() {
  if (!props.alumno) return
  const importe = Number(form.importe)
  const cuota = selectedCuota.value
  if (cuota && importe > Number(cuota.saldo)) {
    const confirmation = await confirmSaldoAFavor({
      importe,
      saldo: Number(cuota.saldo),
      importeAplicado: Number(cuota.saldo),
      saldoFavor: importe - Number(cuota.saldo),
    })
    if (!confirmation.isConfirmed) return
  }
  saving.value = true
  try {
    await createPago({
      alumno: props.alumno.id,
      cuota: form.cuota || null,
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
