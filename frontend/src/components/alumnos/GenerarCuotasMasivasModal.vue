<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="requestClose">
      <form
        v-focus-trap="{ close: requestClose, busy: saving }"
        v-form-validation
        class="modal-card compact-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cuotas-masivas-title"
        :aria-busy="saving || loading"
        @submit.prevent="handleSubmit"
      >
        <header class="modal-head">
          <div>
            <p class="eyebrow">Cuotas</p>
            <h2 id="cuotas-masivas-title">Generar cuotas masivas</h2>
            <span>Seleccioná el grupo a procesar</span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar formulario" @click="requestClose">
            <XMarkIcon aria-hidden="true" />
          </button>
        </header>

        <section class="modal-section">
          <div class="modal-grid">
            <label>
              Sucursal
              <select v-model="form.sucursal" required>
                <option value="" disabled>Seleccionar sucursal</option>
                <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
                  {{ sucursal.nombre }}
                </option>
              </select>
            </label>
            <label>
              Carrera/curso (opcional)
              <select v-model="form.carrera">
                <option value="">Todas</option>
                <option v-for="carrera in carrerasFiltradas" :key="carrera.id" :value="carrera.id">
                  {{ carrera.nombre }}
                </option>
              </select>
            </label>
            <label>
              Concepto
              <select v-model="form.concepto" required>
                <option value="" disabled>Seleccionar concepto</option>
                <option v-for="concepto in conceptosFiltrados" :key="concepto.id" :value="concepto.id">
                  {{ concepto.nombre }}
                </option>
              </select>
            </label>
            <label>
              Mes correspondiente
              <input v-model="form.periodo" type="date" required />
              <small class="field-help">Elegí cualquier fecha del mes al que corresponde la cuota; el día no modifica el período.</small>
            </label>
            <label>
              Fecha de emisión
              <input v-model="form.fecha_emision" type="date" required />
            </label>
            <label>
              Vencimiento
              <input v-model="form.fecha_vencimiento" type="date" required />
            </label>
            <label>
              Importe
              <input v-model="form.importe" type="number" min="0" step="0.01" required />
            </label>
            <label>
              Tipo de descuento
              <select v-model="form.tipo_descuento"><option value="">Sin descuento</option><option v-for="tipo in tiposFiltrados" :key="tipo.id" :value="tipo.id">{{ tipo.nombre }}</option></select>
            </label>
            <label v-if="form.tipo_descuento">Descuento<input v-model="form.descuento" type="number" min="0" step="0.01" :readonly="selectedDiscount?.valor > 0" /></label>
            <label v-if="form.tipo_descuento">Motivo del descuento<input v-model.trim="form.motivo_descuento" required placeholder="Ej. Convenio vigente" /></label>
            <label>
              Recargo
              <input v-model="form.recargo" type="number" min="0" step="0.01" />
            </label>
          </div>
        </section>

        <section class="massive-fee-summary" aria-live="polite">
          <strong v-if="loading">Calculando alumnos activos…</strong>
          <template v-else>
            <strong>{{ alumnosElegibles.length }} alumnos serán afectados</strong>
            <span v-if="alumnosEncontrados && omitidas">
              {{ omitidas }} ya tienen esta cuota y serán omitidos.
            </span>
            <span v-else-if="!alumnosElegibles.length">No hay alumnos activos elegibles para este filtro.</span>
          </template>
          <p v-if="error" class="students-inline-error" role="alert">{{ error }}</p>
        </section>

        <footer class="modal-actions">
          <button class="secondary-button" type="button" :disabled="saving || loading" @click="requestClose">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="saving || loading || !alumnosElegibles.length" type="submit">
            <AppButtonContent :loading="saving" label="Revisar generación" loading-label="Generando" />
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
import { useCuotasMasivas } from '@/composables/useCuotasMasivas'
import { useToast } from '@/composables/useToast'
import { confirmGeneracionCuotasMasivas, showResultadoCuotasMasivas } from '@/lib/swal'
import AppButtonContent from '@/components/ui/AppButtonContent.vue'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'
import { useCatalogos } from '@/composables/useCatalogos'

const props = defineProps({
  open: { type: Boolean, default: false },
  sucursales: { type: Array, default: () => [] },
  carreras: { type: Array, default: () => [] },
  conceptos: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'saved'])
const toast = useToast()
const { alumnosElegibles, alumnosEncontrados, omitidas, loading, error, evaluar, generar } = useCuotasMasivas()
const { tiposDescuento } = useCatalogos()

const form = reactive({
  sucursal: '',
  carrera: '',
  concepto: '',
  periodo: '',
  fecha_emision: '',
  fecha_vencimiento: '',
  importe: '',
  descuento: 0,
  tipo_descuento: '',
  motivo_descuento: '',
  recargo: 0,
})
const saving = ref(false)

const carrerasFiltradas = computed(() => props.carreras.filter(
  (carrera) => String(carrera.sucursal) === String(form.sucursal),
))

const conceptosFiltrados = computed(() => props.conceptos.filter(
  (concepto) => concepto.activo && String(concepto.sucursal) === String(form.sucursal),
))

const conceptoSeleccionado = computed(() => conceptosFiltrados.value.find(
  (concepto) => String(concepto.id) === String(form.concepto),
))
const tiposFiltrados = computed(() => tiposDescuento.value.filter((tipo) => tipo.activo && String(tipo.sucursal) === String(form.sucursal)))
const selectedDiscount = computed(() => tiposFiltrados.value.find((tipo) => String(tipo.id) === String(form.tipo_descuento)))

const totalUnitario = computed(() => Math.max(
  Number(form.importe || 0) - Number(form.descuento || 0) + Number(form.recargo || 0),
  0,
))

const totalEstimado = computed(() => totalUnitario.value * alumnosElegibles.value.length)

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function resetForm() {
  form.sucursal = props.sucursales[0]?.id || ''
  form.carrera = ''
  form.concepto = ''
  form.periodo = ''
  form.fecha_emision = todayStr()
  form.fecha_vencimiento = ''
  form.importe = ''
  form.descuento = 0
  form.tipo_descuento = ''
  form.motivo_descuento = ''
  form.recargo = 0
}

function requestClose() {
  if (!saving.value) emit('close')
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) resetForm()
  },
)

watch([() => form.tipo_descuento, () => form.importe], () => {
  const tipo = selectedDiscount.value
  if (!tipo) { form.descuento = 0; return }
  if (Number(tipo.valor) <= 0) return
  form.descuento = tipo.modalidad === 'porcentaje'
    ? (Number(form.importe || 0) * Number(tipo.valor) / 100).toFixed(2)
    : Math.min(Number(tipo.valor), Number(form.importe || 0)).toFixed(2)
})

watch(
  () => form.sucursal,
  () => {
    if (!props.open) return
    form.carrera = ''
    form.concepto = conceptosFiltrados.value[0]?.id || ''
  },
)

watch(
  () => form.concepto,
  (conceptoId) => {
    const concepto = conceptosFiltrados.value.find((item) => String(item.id) === String(conceptoId))
    if (concepto) form.importe = concepto.importe
  },
)

watch(
  () => [props.open, form.sucursal, form.carrera, form.concepto, form.periodo],
  async ([isOpen]) => {
    if (!isOpen) return
    await evaluar({
      sucursal: form.sucursal,
      carrera: form.carrera,
      concepto: form.concepto,
      periodo: periodoParaBackend(form.periodo),
    })
  },
)

async function handleSubmit() {
  const sucursal = props.sucursales.find((item) => String(item.id) === String(form.sucursal))
  const carrera = carrerasFiltradas.value.find((item) => String(item.id) === String(form.carrera))
  const confirmation = await confirmGeneracionCuotasMasivas({
    cantidad: alumnosElegibles.value.length,
    sucursal: sucursal?.nombre || 'Sin sucursal',
    carrera: carrera?.nombre || 'Todas',
    concepto: conceptoSeleccionado.value?.nombre || 'Sin concepto',
    periodo: form.periodo,
    importe: form.importe,
    totalEstimado: totalEstimado.value,
  })
  if (!confirmation.isConfirmed) return

  saving.value = true
  try {
    const response = await generar({
      alumnos: alumnosElegibles.value.map((alumno) => alumno.id),
      concepto: form.concepto,
      periodo: periodoParaBackend(form.periodo),
      fecha_emision: form.fecha_emision,
      fecha_vencimiento: form.fecha_vencimiento,
      importe: form.importe,
      descuento: form.descuento || 0,
      tipo_descuento: form.tipo_descuento || null,
      motivo_descuento: form.motivo_descuento,
      recargo: form.recargo || 0,
    })
    const creadas = Array.isArray(response) ? response.length : alumnosElegibles.value.length
    const resultado = { creadas, omitidas: omitidas.value, errores: 0 }
    if (resultado.omitidas) {
      await showResultadoCuotasMasivas(resultado)
    } else {
      toast.success(`${creadas} cuotas generadas correctamente.`)
    }
    emit('saved', resultado)
    emit('close')
  } catch (err) {
    await showResultadoCuotasMasivas({
      creadas: 0,
      omitidas: omitidas.value,
      errores: alumnosElegibles.value.length,
      detalle: err.message || 'No se pudieron generar las cuotas.',
    })
  } finally {
    saving.value = false
  }
}

function periodoParaBackend(value) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(value || '')) return value.slice(0, 7)
  const match = /^(\d{2})-(\d{2})-(\d{4})$/.exec(value || '')
  return match ? `${match[3]}-${match[2]}` : value
}
</script>
