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
              <select
                v-model="form.tipo_descuento"
                :disabled="isDiscountCatalogLoading"
                :aria-busy="isDiscountCatalogLoading"
              >
                <option value="">Sin descuento</option>
                <option v-for="tipo in tiposFiltrados" :key="tipo.id" :value="tipo.id">{{ tipo.nombre }}</option>
              </select>
              <small v-if="isDiscountCatalogLoading" class="field-help" role="status">Cargando tipos de descuento...</small>
              <small v-else-if="discountCatalogErrorMessage" class="field-help field-error" role="alert">{{ discountCatalogErrorMessage }}</small>
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
            <strong>{{ alumnosElegibles.length }} alumnos elegibles · {{ omitidas }} omitidos</strong>
            <dl class="massive-fee-summary-details">
              <div><dt>Sucursal</dt><dd>{{ sucursalSeleccionada?.nombre || 'Elegí una sucursal' }}</dd></div>
              <div><dt>Carrera/curso</dt><dd>{{ carreraSeleccionada?.nombre || 'Todas' }}</dd></div>
              <div><dt>Concepto</dt><dd>{{ conceptoSeleccionado?.nombre || 'Sin seleccionar' }}</dd></div>
              <div><dt>Período</dt><dd>{{ periodoParaBackend(form.periodo) || 'Sin seleccionar' }}</dd></div>
              <div><dt>Importe unitario</dt><dd>{{ formatCurrency(form.importe) }}</dd></div>
              <div><dt>Descuento</dt><dd>− {{ formatCurrency(form.descuento) }}</dd></div>
              <div><dt>Recargo</dt><dd>+ {{ formatCurrency(form.recargo) }}</dd></div>
              <div><dt>Total estimado</dt><dd>{{ formatCurrency(totalEstimado) }}</dd></div>
            </dl>
            <span v-if="!alumnosEncontrados && !loading">No hay alumnos activos que coincidan con este filtro.</span>
          </template>
          <p v-if="error" class="students-inline-error" role="alert">{{ error }}</p>
        </section>

        <section v-if="!loading && detalleAlumnos.length" class="massive-fee-preview" aria-label="Detalle de la previsualización">
          <div class="massive-fee-preview-tabs" role="tablist" aria-label="Alumnos de la generación">
            <button
              id="massive-fee-eligible-tab"
              type="button"
              role="tab"
              :aria-selected="previewTab === 'elegibles'"
              :tabindex="previewTab === 'elegibles' ? 0 : -1"
              aria-controls="massive-fee-preview-list"
              @keydown="handlePreviewTabKeydown($event, 'elegibles')"
              @click="setPreviewTab('elegibles')"
            >Elegibles ({{ alumnosElegibles.length }})</button>
            <button
              id="massive-fee-omitted-tab"
              type="button"
              role="tab"
              :aria-selected="previewTab === 'omitidos'"
              :tabindex="previewTab === 'omitidos' ? 0 : -1"
              aria-controls="massive-fee-preview-list"
              @keydown="handlePreviewTabKeydown($event, 'omitidos')"
              @click="setPreviewTab('omitidos')"
            >Omitidos ({{ omitidosDetalle.length }})</button>
          </div>
          <ul id="massive-fee-preview-list" class="massive-fee-preview-list" role="tabpanel" tabindex="0" :aria-labelledby="previewTab === 'elegibles' ? 'massive-fee-eligible-tab' : 'massive-fee-omitted-tab'">
            <li v-for="alumno in previewPageItems" :key="alumno.id">
              <span class="massive-fee-preview-identity">
                <strong>{{ alumno.nombre_completo }}</strong>
                <small>Legajo {{ alumno.legajo }} · {{ alumno.carrera_nombre || 'Sin carrera asignada' }} · {{ alumno.estado }}</small>
              </span>
              <span v-if="previewTab === 'omitidos'" class="massive-fee-omission">{{ alumno.motivo }}</span>
            </li>
            <li v-if="!previewPageItems.length" class="massive-fee-preview-empty">
              {{ previewTab === 'omitidos' ? 'No hay alumnos omitidos.' : 'No hay alumnos elegibles.' }}
            </li>
          </ul>
          <nav v-if="previewTotalPages > 1" class="massive-fee-preview-pagination" aria-label="Páginas del detalle de alumnos">
            <button type="button" :disabled="previewPage <= 1" @click="previewPage -= 1">Anterior</button>
            <span aria-live="polite">Página {{ previewPage }} de {{ previewTotalPages }}</span>
            <button type="button" :disabled="previewPage >= previewTotalPages" @click="previewPage += 1">Siguiente</button>
          </nav>
        </section>

        <footer class="modal-actions">
          <button class="secondary-button" type="button" :disabled="saving || loading" @click="requestClose">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="saving || loading || !alumnosElegibles.length" type="submit">
            <AppButtonContent :loading="saving" label="Revisar generación" loading-label="Generando" />
          </button>
        </footer>
      </form>
      </div>
    </AppModalTransition>
  </Teleport>
</template>

<style scoped>
.field-help {
  display: block;
  margin-top: 5px;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.35;
}

.field-error {
  color: var(--danger);
}

.massive-fee-summary {
  margin: 0 24px 24px;
  padding: 14px 16px;
  display: grid;
  gap: 5px;
  border: 1px solid color-mix(in srgb, var(--primary) 18%, var(--border));
  border-radius: 12px;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--primary-soft) 68%, var(--surface));
  font-size: 12px;
  line-height: 1.4;
}

.massive-fee-summary strong {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 750;
}

.massive-fee-summary span {
  display: block;
}

.massive-fee-summary-details {
  margin: 6px 0 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 16px;
}

.massive-fee-summary-details > div { min-width: 0; }
.massive-fee-summary-details dt { color: var(--text-secondary); }
.massive-fee-summary-details dd { margin: 2px 0 0; color: var(--text-primary); font-weight: 700; overflow-wrap: anywhere; }

.massive-fee-preview {
  margin: 0 24px 24px;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
}

.massive-fee-preview-tabs { display: flex; gap: 4px; padding: 6px; border-bottom: 1px solid var(--border); background: var(--surface-soft); }
.massive-fee-preview-tabs button { min-height: 44px; flex: 1; border: 0; border-radius: 8px; color: var(--text-secondary); background: transparent; font-weight: 750; }
.massive-fee-preview-tabs button[aria-selected="true"] { color: var(--primary); background: var(--surface); box-shadow: var(--shadow); }
.massive-fee-preview-tabs button:focus-visible,
.massive-fee-preview-list:focus-visible,
.massive-fee-preview-pagination button:focus-visible { outline: 3px solid var(--primary); outline-offset: 2px; }
.massive-fee-preview-list { max-height: 230px; overflow-y: auto; margin: 0; padding: 0 16px; list-style: none; }
.massive-fee-preview-list li { min-height: 56px; display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--border); }
.massive-fee-preview-list li:last-child { border-bottom: 0; }
.massive-fee-preview-identity { min-width: 0; display: grid; gap: 3px; }
.massive-fee-preview-identity strong { color: var(--text-primary); overflow-wrap: anywhere; }
.massive-fee-preview-identity small { color: var(--text-secondary); font-size: 12px; }
.massive-fee-omission { max-width: 42%; color: var(--danger); font-size: 12px; text-align: right; }
.massive-fee-preview-empty { color: var(--text-secondary); justify-content: center !important; text-align: center; }
.massive-fee-preview-pagination { min-height: 48px; display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 6px 12px; border-top: 1px solid var(--border); color: var(--text-secondary); font-size: 12px; }
.massive-fee-preview-pagination button { min-height: 44px; padding: 0 10px; border: 1px solid var(--border); border-radius: 8px; color: var(--text-primary); background: var(--surface); font-weight: 700; }
.massive-fee-preview-pagination button:disabled { opacity: .5; cursor: not-allowed; }

.massive-fee-summary .students-inline-error {
  margin: 2px 0 0;
}

@media (max-width: 560px) {
  .massive-fee-summary {
    margin-right: 16px;
    margin-left: 16px;
  }

  .massive-fee-preview { margin-right: 16px; margin-left: 16px; }
  .massive-fee-summary-details { grid-template-columns: 1fr; }
  .massive-fee-preview-list li { align-items: flex-start; flex-direction: column; }
  .massive-fee-omission { max-width: none; text-align: left; }
}
</style>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import { useCuotasMasivas } from '@/composables/useCuotasMasivas'
import AppModalTransition from '@/components/ui/AppModalTransition.vue'
import { useToast } from '@/composables/useToast'
import { confirmGeneracionCuotasMasivas, showResultadoCuotasMasivas } from '@/lib/swal'
import AppButtonContent from '@/components/ui/AppButtonContent.vue'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'
import { useCatalogos } from '@/composables/useCatalogos'
import { useAuth } from '@/composables/useAuth'
import { toLocalISODate } from '@/lib/formatters'

const props = defineProps({
  open: { type: Boolean, default: false },
  sucursales: { type: Array, default: () => [] },
  carreras: { type: Array, default: () => [] },
  conceptos: { type: Array, default: () => [] },
  tiposDescuentoLoading: { type: Boolean, default: false },
  tiposDescuentoError: { type: String, default: '' },
})

const emit = defineEmits(['close', 'saved'])
const toast = useToast()
const { alumnosElegibles, alumnosEncontrados, omitidas, detalleAlumnos, loading, error, evaluar, generar } = useCuotasMasivas()
const { tiposDescuento } = useCatalogos()
const { user } = useAuth()
const isDiscountCatalogLoading = computed(() => props.tiposDescuentoLoading)
const discountCatalogErrorMessage = computed(() => props.tiposDescuentoError)

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
const previewTab = ref('elegibles')
const previewPage = ref(1)

const sucursalSeleccionada = computed(() => props.sucursales.find(
  (item) => String(item.id) === String(form.sucursal),
))
const carreraSeleccionada = computed(() => carrerasFiltradas.value.find(
  (item) => String(item.id) === String(form.carrera),
))
const omitidosDetalle = computed(() => detalleAlumnos.value.filter((alumno) => alumno.motivo))
const previewRows = computed(() => previewTab.value === 'omitidos'
  ? omitidosDetalle.value
  : detalleAlumnos.value.filter((alumno) => !alumno.motivo))
const previewTotalPages = computed(() => Math.max(1, Math.ceil(previewRows.value.length / 10)))
const previewPageItems = computed(() => previewRows.value.slice((previewPage.value - 1) * 10, previewPage.value * 10))

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
  return toLocalISODate()
}

function resetForm() {
  const profileBranchId = user.value?.perfil?.sucursal?.id
  form.sucursal = props.sucursales.find((item) => String(item.id) === String(profileBranchId))?.id || ''
  form.carrera = ''
  form.concepto = conceptosFiltrados.value[0]?.id || ''
  form.periodo = ''
  form.fecha_emision = todayStr()
  form.fecha_vencimiento = ''
  form.importe = conceptoSeleccionado.value?.importe || ''
  form.descuento = 0
  form.tipo_descuento = ''
  form.motivo_descuento = ''
  form.recargo = 0
  previewTab.value = 'elegibles'
  previewPage.value = 1
}

function setPreviewTab(tab) {
  previewTab.value = tab
  previewPage.value = 1
}

function handlePreviewTabKeydown(event, currentTab) {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  const nextTab = event.key === 'Home'
    ? 'elegibles'
    : event.key === 'End'
      ? 'omitidos'
      : currentTab === 'elegibles' ? 'omitidos' : 'elegibles'
  setPreviewTab(nextTab)
  nextTick(() => document.getElementById(`massive-fee-${nextTab === 'elegibles' ? 'eligible' : 'omitted'}-tab`)?.focus())
}

function formatCurrency(value) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', minimumFractionDigits: 2 }).format(Number(value || 0))
}

function requestClose() {
  if (!saving.value) emit('close')
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) resetForm()
  },
  { immediate: true },
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
  { immediate: true },
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

watch([previewRows], () => {
  if (previewPage.value > previewTotalPages.value) previewPage.value = previewTotalPages.value
})

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
    descuento: form.descuento,
    recargo: form.recargo,
    totalEstimado: totalEstimado.value,
    omitidas: omitidas.value,
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
