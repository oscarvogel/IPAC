<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="$emit('close')">
      <form class="modal-card compact-modal" @submit.prevent="handleSubmit">
        <header class="modal-head">
          <div>
            <p class="eyebrow">Cuotas</p>
            <h2>Generar cuota</h2>
            <span v-if="alumno">{{ alumno.apellido }}, {{ alumno.nombre }}</span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar" @click="$emit('close')">&times;</button>
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
              Periodo
              <input v-model="form.periodo" placeholder="ej. 2026-08" required />
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
            </label>
            <label>
              Recargo
              <input v-model="form.recargo" type="number" min="0" step="0.01" value="0" />
            </label>
          </div>
        </section>

        <footer class="modal-actions">
          <button class="secondary-button" type="button" @click="$emit('close')">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="saving" type="submit">
            {{ saving ? 'Generando...' : 'Generar cuota' }}
          </button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { usePagos } from '@/composables/usePagos'
import { useToast } from '@/composables/useToast'

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
      periodo: form.periodo,
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
</script>
