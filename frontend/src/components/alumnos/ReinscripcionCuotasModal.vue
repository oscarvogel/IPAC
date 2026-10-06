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
          aria-labelledby="reinscripcion-title"
          :aria-busy="saving || loading"
          @submit.prevent="handleSubmit"
        >
          <header class="modal-head">
            <div>
              <p class="eyebrow">Reinscripción</p>
              <h2 id="reinscripcion-title">Generar las cuotas del año</h2>
              <span v-if="alumno">{{ alumno.apellido }}, {{ alumno.nombre }}</span>
            </div>
            <button class="icon-button" type="button" aria-label="Cerrar formulario" @click="requestClose">
              <XMarkIcon aria-hidden="true" />
            </button>
          </header>

          <section class="modal-section">
            <p v-if="loading" class="reinscripcion-estado" role="status">Calculando el plan de la carrera...</p>
            <template v-else>
              <div class="modal-grid">
                <label class="reinscripcion-carrera">
                  Carrera
                  <input :value="plan?.carrera_nombre || 'Sin carrera'" disabled />
                </label>
                <label>
                  Concepto a cobrar
                  <select v-model="form.concepto" required :disabled="!conceptosDisponibles.length">
                    <option v-if="!conceptosDisponibles.length" value="">Sin concepto de cuota</option>
                    <option v-for="concepto in conceptosDisponibles" :key="concepto.id" :value="concepto.id">
                      {{ concepto.nombre }} — {{ formatCurrency(concepto.importe) }}
                    </option>
                  </select>
                </label>
                <label>
                  Cantidad de cuotas
                  <input v-model.number="form.cantidad" type="number" min="1" max="24" required />
                  <small v-if="planSinPlan" class="field-help field-error">
                    {{ plan.motivo_sin_plan }}
                  </small>
                  <small v-else class="field-help">
                    El plan de la carrera propone {{ plan.plan_cuotas }}. Cámbialo si este alumno debe menos.
                  </small>
                </label>
                <label class="reinscripcion-mes-inicial">
                  Mes inicial
                  <input :value="mesInicialLegible" disabled />
                  <small class="field-help">Sale de la fecha de inicio de la matrícula ({{ formatDate(matricula?.fecha_inicio) || '—' }}).</small>
                </label>
                <label>
                  Día de vencimiento
                  <input v-model.number="form.dia_vencimiento" type="number" min="1" max="28" required />
                  <small class="field-help">El 10 es el día que maneja IPAC. Máximo 28 para que febrero siempre tenga fecha.</small>
                </label>
                <label>
                  Fecha de emisión
                  <input v-model="form.fecha_emision" type="date" required />
                </label>
              </div>

              <ul v-if="etiquetasPeriodo.length" class="reinscripcion-periodos" aria-label="Períodos a generar">
                <li v-for="etiqueta in etiquetasPeriodo" :key="etiqueta">{{ etiqueta }}</li>
              </ul>
            </template>
          </section>

          <section class="massive-fee-summary" aria-live="polite">
            <template v-if="loading">
              <strong>Calculando.</strong>
            </template>
            <template v-else>
              <strong v-if="!conceptosDisponibles.length" class="reinscripcion-bloqueo">
                La carrera no tiene un concepto de cuota cargado.
              </strong>
              <template v-else-if="periodos.length">
                <strong>{{ periodos.length }} {{ periodos.length === 1 ? 'período' : 'períodos' }}</strong>
                <p v-if="previewLoading" class="reinscripcion-estado">Revisando qué cuotas ya tiene el alumno.</p>
                <p v-else-if="omitidas > 0" class="reinscripcion-parcial">
                  {{ omitidas }} ya existen y se van a saltear. Se generan <strong>{{ cuotasAGenerar }}</strong>.
                </p>
                <p v-else-if="cuotasAGenerar > 0" class="reinscripcion-resumen">
                  Se generan <strong>{{ cuotasAGenerar }} {{ cuotasAGenerar === 1 ? 'cuota' : 'cuotas' }}</strong>.
                </p>
                <p v-else class="reinscripcion-estado">
                  No se pudo calcular el preview. Podés generar igual: lo que ya exista se saltea.
                </p>
              </template>
              <!--
                Sin periodos no hay nada calculando: falta la cantidad. Decirlo
                es lo que evita el "Calculando..." eterno de una carrera sin plan.
              -->
              <span v-else-if="cantidadInvalida" class="reinscripcion-estado">
                Indicá cuántas cuotas se generan para ver los períodos.
              </span>
              <span v-else class="reinscripcion-estado">Sin períodos para este lote.</span>
            </template>
            <p v-if="error" class="students-inline-error" role="alert">{{ error }}</p>
          </section>

          <footer class="modal-actions">
            <button class="secondary-button" type="button" :disabled="saving || loading" @click="requestClose">Cancelar</button>
            <button
              class="primary-button modal-submit"
              type="submit"
              :disabled="saving || loading || !puedeGenerar"
            >
              <AppButtonContent :loading="saving" label="Generar cuotas" loading-label="Generando" />
            </button>
          </footer>
        </form>
      </div>
    </AppModalTransition>
  </Teleport>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import AppModalTransition from '@/components/ui/AppModalTransition.vue'
import AppButtonContent from '@/components/ui/AppButtonContent.vue'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'
import { useMatriculas } from '@/composables/useMatriculas'
import { useCuotasMasivas } from '@/composables/useCuotasMasivas'
import { useToast } from '@/composables/useToast'
import { confirmReinscripcionCuotas } from '@/lib/swal'
import { formatDate, toLocalISODate } from '@/lib/formatters'

const props = defineProps({
  open: { type: Boolean, default: false },
  alumno: { type: Object, default: null },
  matricula: { type: Object, default: null },
})

const emit = defineEmits(['close', 'saved'])
const toast = useToast()
const { cargarPlanCuotas, generarCuotasDeMatricula } = useMatriculas()
const { periodos, etiquetasPeriodo, cuotasAGenerar, loading: previewLoading, error, evaluar } = useCuotasMasivas()

const plan = ref(null)
const loading = ref(false)
const saving = ref(false)

const form = reactive({
  concepto: '',
  cantidad: 10,
  dia_vencimiento: 10,
  fecha_emision: toLocalISODate(),
})

const conceptosDisponibles = computed(() => plan.value?.conceptos || [])
const planSinPlan = computed(() => Boolean(plan.value && !plan.value.periodos.length))
/**
 * El mes inicial sale del plan que propuso el backend, no de la
 * previsualizacion: cuando se abre el formulario la previsualizacion todavia
 * no corrio, y leerla aca dejaria el formulario sin mes hasta que el operador
 * tocara algo.
 *
 * Cuando la carrera no tiene plan el backend no propone ningun periodo, pero
 * la reinscripcion igual arranca en el mes de la matricula: es la misma regla
 * que aplica al generar. Sin este fallback el formulario se quedaba sin mes,
 * sin previsualizacion y con "Calculando..." para siempre.
 */
const periodoInicial = computed(() => {
  const propuesto = plan.value?.periodos?.[0]
  if (propuesto) return propuesto
  return primerPeriodoDe(props.matricula?.fecha_inicio)
})
const mesInicialLegible = computed(() => {
  const primero = periodoInicial.value
  if (!primero) return 'Sin determinar'
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ]
  return `${meses[Number(primero.slice(5, 7)) - 1]} ${primero.slice(0, 4)}`
})
const omitidas = computed(() => {
  const total = periodos.value.length
  return Math.max(0, total - cuotasAGenerar.value)
})
const cantidadInvalida = computed(() => !Number(form.cantidad))
/**
 * No alcanza con que haya una cantidad escrita: tiene que haber una
 * previsualizacion que produjo periodos. Sin eso el boton dejaba confirmar
 * "Generar 0 cuotas" contra una carrera sin plan, que es deuda que el alumno
 * no contrajo. Un error de calculo tambien bloquea: si no sabemos que se va
 * a generar, no se envia nada.
 */
const puedeGenerar = computed(() => Boolean(
  props.matricula
  && conceptosDisponibles.value.length
  && form.concepto
  && Number(form.cantidad) > 0
  && periodos.value.length > 0
  && !previewLoading.value
  && !error.value
  && !loading.value,
))

function formatCurrency(value) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(Number(value || 0))
}

/**
 * `YYYY-MM-DD` (o `YYYY-MM`) a `YYYY-MM`. La fecha de inicio de la matrícula
 * es la que define el arranque del lote, haya plan de carrera o no.
 */
function primerPeriodoDe(fecha) {
  if (typeof fecha !== 'string' || fecha.length < 7) return ''
  return fecha.slice(0, 7)
}

/**
 * Traduce el plan que propone el backend a los campos que espera la
 * previsualización. El mes inicial sale del primer período devuelto, no de un
 * campo aparte: si el backend propone otra cosa, la previsualización tiene que
 * mirar lo mismo que la generación.
 */
function planParaPrevisualizar() {
  const primero = periodoInicial.value
  const cantidad = Number(form.cantidad)
  if (!primero || !cantidad) return null
  return {
    cantidad,
    mes_inicial: Number(primero.slice(5, 7)),
    anio_inicial: Number(primero.slice(0, 4)),
    dia_vencimiento: Number(form.dia_vencimiento),
  }
}

async function refrescarPrevisualizacion() {
  if (!props.open || !props.alumno || !props.matricula || !form.concepto) return
  const planPayload = planParaPrevisualizar()
  if (!planPayload) return
  await evaluar({
    sucursal: props.matricula.sucursal,
    carrera: props.matricula.carrera,
    concepto: form.concepto,
    alumno: props.alumno.id,
    plan: planPayload,
  })
}

async function cargar() {
  loading.value = true
  error.value = ''
  try {
    const data = await cargarPlanCuotas(props.matricula.id)
    plan.value = data
    // Sin plan no se inventa una cantidad: el campo queda vacio y el operador
    // decide. Prefijarla con 1 hacia que la previsualizacion corriera sobre un
    // numero que el sistema no sabe.
    form.cantidad = data.periodos.length || data.plan_cuotas || ''
    form.concepto = data.conceptos[0]?.id || ''
    form.dia_vencimiento = 10
    form.fecha_emision = toLocalISODate()
    await refrescarPrevisualizacion()
  } catch (err) {
    error.value = err.message || 'No se pudo calcular el plan de la carrera.'
  } finally {
    loading.value = false
  }
}

function requestClose() {
  if (!saving.value) emit('close')
}

watch(
  () => [props.open, props.matricula?.id],
  ([isOpen]) => {
    if (isOpen) cargar()
  },
  { immediate: true },
)

watch(
  () => [form.concepto, form.cantidad, form.dia_vencimiento],
  () => {
    if (props.open) refrescarPrevisualizacion()
  },
)

async function handleSubmit() {
  if (!props.matricula || !puedeGenerar.value) return
  const planPayload = planParaPrevisualizar()
  const concepto = conceptosDisponibles.value.find((item) => String(item.id) === String(form.concepto))
  const confirmacion = await confirmReinscripcionCuotas({
    alumno: `${props.alumno.apellido}, ${props.alumno.nombre}`,
    carrera: plan.value?.carrera_nombre || '—',
    concepto: concepto?.nombre || '—',
    periodos: periodos.value.length
      ? `${periodos.value[0]} a ${periodos.value[periodos.value.length - 1]} (${periodos.value.length})`
      : '—',
    cantidad: cuotasAGenerar.value,
    importe: concepto?.importe,
    omitidas: omitidas.value,
  })
  if (!confirmacion.isConfirmed) return

  saving.value = true
  try {
    const respuesta = await generarCuotasDeMatricula(props.matricula.id, {
      concepto: form.concepto,
      cantidad: planPayload.cantidad,
      dia_vencimiento: planPayload.dia_vencimiento,
      fecha_emision: form.fecha_emision,
    })
    const resumen = respuesta?.resumen || {}
    const creadas = Number(resumen.creadas || 0)
    const salteadas = Number(resumen.omitidas || 0)
    if (!creadas) {
      toast.warning('El alumno ya tenía todas las cuotas de este lote.')
    } else if (salteadas) {
      toast.success(`${creadas} cuotas generadas. ${salteadas} ya existían y se saltearon.`)
    } else {
      toast.success(`${creadas} cuotas generadas correctamente.`)
    }
    emit('saved', { creadas, omitidas: salteadas })
    emit('close')
  } catch (err) {
    toast.error(err.message || 'No se pudieron generar las cuotas.')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.field-help {
  display: block;
  margin-top: 5px;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.35;
}

.field-error { color: var(--danger); }

.reinscripcion-carrera { grid-column: 1 / -1; }

.reinscripcion-estado { margin: 0; color: var(--text-secondary); font-size: 13px; }

.reinscripcion-periodos {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}

.reinscripcion-periodos li {
  padding: 4px 9px;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--text-secondary);
  background: var(--surface-soft);
  font-size: 12px;
}

.massive-fee-summary {
  margin: 0 24px 24px;
  padding: 14px 16px;
  display: grid;
  gap: 6px;
  border: 1px solid color-mix(in srgb, var(--primary) 18%, var(--border));
  border-radius: 12px;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--primary-soft) 68%, var(--surface));
  font-size: 13px;
  line-height: 1.4;
}

.massive-fee-summary p { margin: 0; }
.massive-fee-summary strong { color: var(--text-primary); }
.reinscripcion-resumen strong,
.reinscripcion-parcial strong { color: var(--primary); }
.reinscripcion-bloqueo { color: var(--danger); }

@media (max-width: 560px) {
  .massive-fee-summary { margin-right: 16px; margin-left: 16px; }
}
</style>
