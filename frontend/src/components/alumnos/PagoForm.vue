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
              Concepto
              <select v-model="form.concepto">
                <option value="">Pago a cuenta</option>
                <option v-for="c in availableConceptos" :key="c.id" :value="c.id">
                  {{ c.nombre }} · $ {{ c.importe }}
                </option>
              </select>
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

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import { usePagos } from '@/composables/usePagos'
import { useToast } from '@/composables/useToast'
import AppButtonContent from '@/components/ui/AppButtonContent.vue'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'

const props = defineProps({
  open: { type: Boolean, default: false },
  alumno: { type: Object, default: null },
  conceptos: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'saved'])

const { createPago, loadPagos } = usePagos()
const toast = useToast()

const form = reactive({
  concepto: '',
  importe: '',
  medio: 'efectivo',
  observacion: '',
})

const saving = ref(false)

function requestClose() {
  if (!saving.value) emit('close')
}

const availableConceptos = computed(() => {
  if (!props.alumno) return []
  return props.conceptos
    .filter((c) => c.activo && c.sucursal === props.alumno.sucursal)
})

watch(
  () => [props.open, availableConceptos.value],
  ([isOpen, conceptos]) => {
    if (!isOpen) return
    const first = conceptos[0]
    form.concepto = first?.id || ''
    form.importe = first?.importe || ''
    form.medio = 'efectivo'
    form.observacion = ''
  },
  { immediate: true },
)

async function handleSubmit() {
  if (!props.alumno) return
  saving.value = true
  try {
    await createPago({
      alumno: props.alumno.id,
      concepto: form.concepto || null,
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
