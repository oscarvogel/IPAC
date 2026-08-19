<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="requestClose">
      <form
        v-focus-trap="{ close: requestClose, busy: saving }"
        v-form-validation
        class="modal-card compact-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cuota-form-title"
        :aria-busy="saving"
        @submit.prevent="handleSubmit"
      >
        <header class="modal-head">
          <div>
            <p class="eyebrow">Cuotas</p>
            <h2 id="cuota-form-title">Generar cuota</h2>
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
              <select v-model="form.concepto" required>
                <option value="" disabled>Seleccionar concepto</option>
                <option v-for="c in conceptosFiltrados" :key="c.id" :value="c.id">
                  {{ c.nombre }} &middot; $ {{ c.importe }}
                </option>
              </select>
            </label>
            <label>
              Mes correspondiente
              <input
                v-model="form.periodo"
                type="text"
                inputmode="numeric"
                placeholder="DD-MM-YYYY"
                pattern="[0-9]{2}-[0-9]{2}-[0-9]{4}"
                required
              />
              <small class="field-help">Indica a qué mes corresponde esta cuota. Usá el formato DD-MM-YYYY.</small>
            </label>
            <label>
              Fecha de emision
              <input v-model="form.fecha_emision" type="date" required />
            </label>
            <label>
              Fecha de vencimiento
              <input v-model="form.fecha_vencimiento" type="date" required />
            </label>
            <label>
              Importe
              <input v-model="form.importe" type="number" min="0" step="0.01" required />
            </label>
            <label>
              Descuento
              <input v-model="form.descuento" type="number" min="0" step="0.01" value="0" />
              <small class="field-help">Importe que se resta del valor de la cuota. Dejar en $0 si no corresponde.</small>
            </label>
            <label>
              Recargo
              <input v-model="form.recargo" type="number" min="0" step="0.01" value="0" />
              <small class="field-help">Importe adicional que se suma a la cuota. Dejar en $0 si no corresponde.</small>
            </label>
          </div>
        </section>

        <footer class="modal-actions">
          <button class="secondary-button" type="button" :disabled="saving" @click="requestClose">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="saving" type="submit">
            <AppButtonContent :loading="saving" label="Generar cuota" loading-label="Generando…" />
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
import AppButtonContent from '@/components/ui/AppButtonContent.vue'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'

const props = defineProps({
  open: { type: Boolean, default: false },
  alumno: { type: Object, default: null },
  conceptos: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'saved'])

const { generarCuota } = usePagos()
const toast = useToast()

const form = reactive({
  concepto: '',
  periodo: '',
  fecha_emision: '',
  fecha_vencimiento: '',
  importe: '',
  descuento: 0,
  recargo: 0,
})

const saving = ref(false)

function requestClose() {
  if (!saving.value) emit('close')
}

const conceptosFiltrados = computed(() => {
  if (!props.alumno) return []
  return props.conceptos.filter((c) => c.activo && c.sucursal === props.alumno.sucursal)
})

function todayStr() {
  const d = new Date()
  return d.toISOString().slice(0, 10)
}

watch(
  () => [props.open, props.conceptos],
  ([isOpen]) => {
    if (!isOpen) return
    const first = conceptosFiltrados.value[0]
    form.concepto = first?.id || ''
    form.importe = first?.importe || ''
    form.periodo = ''
    form.fecha_emision = todayStr()
    form.fecha_vencimiento = ''
    form.descuento = 0
    form.recargo = 0
  },
  { immediate: true },
)

watch(
  () => form.concepto,
  (id) => {
    if (!id) return
    const c = conceptosFiltrados.value.find((c) => c.id === id)
    if (c) form.importe = c.importe
  },
)

async function handleSubmit() {
  if (!props.alumno) return
  saving.value = true
  try {
    await generarCuota({
      alumnos: [props.alumno.id],
      concepto: form.concepto,
      // La UI usa DD-MM-YYYY; el backend conserva la clave mensual YYYY-MM.
      periodo: periodoParaBackend(form.periodo),
      fecha_emision: form.fecha_emision,
      fecha_vencimiento: form.fecha_vencimiento,
      importe: form.importe,
      descuento: form.descuento || 0,
      recargo: form.recargo || 0,
    })
    toast.success('Cuota generada')
    emit('saved')
    emit('close')
  } catch (err) {
    toast.error(err.message || 'No se pudo generar la cuota.')
  } finally {
    saving.value = false
  }
}

function periodoParaBackend(value) {
  const match = /^(\d{2})-(\d{2})-(\d{4})$/.exec(value || '')
  return match ? `${match[3]}-${match[2]}` : value
}
</script>
