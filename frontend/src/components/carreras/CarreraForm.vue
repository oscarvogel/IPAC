<template>
  <Teleport to="body">
    <AppModalTransition :open="open">
      <div class="modal-backdrop" @click.self="requestClose">
      <form
        v-focus-trap="{ close: requestClose, busy: saving }"
        v-form-validation
        class="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="carrera-form-title"
        :aria-busy="saving"
        @submit.prevent="handleSubmit"
      >
        <header class="modal-head">
          <div>
            <p class="eyebrow">
              {{ editingId ? 'Edición de carrera' : 'Alta de carrera o curso' }}
            </p>
            <h2 id="carrera-form-title">{{ editingId ? 'Editar carrera o curso' : 'Nueva carrera o curso' }}</h2>
            <span class="form-intro">
              Define el plan de estudios y los valores de la cuota. El desglose programático y
              extraprogramático es lo que permite imprimir el reparto que exige el Ministerio de
              Educación en los recibos y las facturas.
            </span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar formulario" @click="requestClose">
            <XMarkIcon aria-hidden="true" />
          </button>
        </header>

        <section class="modal-section">
          <h3>Identificación</h3>
          <div class="modal-grid">
            <label>
              Nombre
              <input v-model="form.nombre" placeholder="Ej. Tecnicatura en Sistemas" required maxlength="160" />
            </label>
            <label>
              Tipo
              <select v-model="form.tipo" required>
                <option value="carrera">Carrera</option>
                <option value="curso">Curso</option>
              </select>
              <small class="field-help">Clasifica si es una carrera de grado o un curso.</small>
            </label>
            <label>
              Sucursal
              <select v-model="form.sucursal" required>
                <option v-for="s in sucursales" :key="s.id" :value="s.id">{{ s.nombre }}</option>
              </select>
              <small class="field-help">La carrera quedará disponible solo en esta sucursal.</small>
            </label>
            <label>
              Duración
              <input v-model="form.duracion" placeholder="Ej. 3 años" maxlength="80" />
            </label>
          </div>
        </section>

        <section class="modal-section">
          <h3>Plan de cuotas</h3>
          <div class="modal-grid">
            <label>
              Cantidad de cuotas
              <input v-model="form.plan_cuotas" type="number" min="0" step="1" placeholder="Ej. 10" />
              <small class="field-help">Número de cuotas del plan, por ejemplo 10.</small>
            </label>
            <label>
              Importe de matrícula
              <input v-model="form.importe_matricula" type="number" min="0" step="0.01" placeholder="0.00" />
            </label>
          </div>
        </section>

        <section class="modal-section">
          <h3>Desglose de la cuota</h3>
          <p class="field-help field-help-block">
            El importe total de la cuota debe figurar desglosado en la parte programática y la
            extraprogramática. Con las dos partes cargadas, el total se calcula solo.
          </p>
          <div class="modal-grid">
            <label>
              Cuota programática
              <input
                v-model="form.cuota_programatica"
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
              />
            </label>
            <label>
              Cuota extraprogramática
              <input
                v-model="form.cuota_extraprogramatica"
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
              />
            </label>
            <label>
              Cuota total
              <input
                v-model="form.cuota_total"
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                @input="totalManual = true"
              />
              <small class="field-help">
                {{ totalManual
                  ? 'Valor cargado a mano: no se recalcula.'
                  : 'Calculado como la suma de las dos partes.' }}
              </small>
            </label>
          </div>
          <p v-if="desgloseIncompleto" class="field-warning" role="status">
            Cargá las dos partes del desglose. Mientras falte una, los recibos de esta carrera se
            emiten sin reparto.
          </p>
          <p v-else-if="totalDescuadrado" class="field-warning" role="status">
            La suma de las dos partes no coincide con la cuota total que cargaste a mano.
          </p>
        </section>

        <section class="modal-section">
          <h3>Convenios</h3>
          <p class="field-help field-help-block">
            Valor de la cuota con descuento por convenio, cuando aplique a esta carrera.
          </p>
          <div class="modal-grid">
            <label>
              Convenio 20 %
              <input v-model="form.cuota_convenio_20" type="number" min="0" step="0.01" placeholder="0.00" />
            </label>
            <label>
              Convenio 15 %
              <input v-model="form.cuota_convenio_15" type="number" min="0" step="0.01" placeholder="0.00" />
            </label>
          </div>
        </section>

        <section class="modal-section">
          <div class="modal-grid">
            <label>
              Descripción
              <textarea v-model="form.descripcion" rows="2" maxlength="255"></textarea>
            </label>
            <label v-if="editingId" class="checkbox-inline">
              <input v-model="form.activa" type="checkbox" />
              Carrera activa
            </label>
          </div>
        </section>

        <footer class="modal-actions">
          <button class="secondary-button" type="button" :disabled="saving" @click="requestClose">
            Cancelar
          </button>
          <button class="primary-button modal-submit" :disabled="saving" type="submit">
            <AppButtonContent
              :loading="saving"
              :label="editingId ? 'Guardar cambios' : 'Crear carrera'"
              loading-label="Guardando."
            />
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
import { useCarreras } from '@/composables/useCarreras'
import { useCatalogos } from '@/composables/useCatalogos'
import { useToast } from '@/composables/useToast'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'

const props = defineProps({
  open: { type: Boolean, default: false },
  carrera: { type: Object, default: null },
})

const emit = defineEmits(['close', 'saved'])

const { createCarrera, updateCarrera } = useCarreras()
const { sucursales } = useCatalogos()
const toast = useToast()

const form = reactive({
  nombre: '',
  tipo: 'carrera',
  sucursal: '',
  duracion: '',
  descripcion: '',
  plan_cuotas: '',
  importe_matricula: '',
  cuota_programatica: '',
  cuota_extraprogramatica: '',
  cuota_total: '',
  cuota_convenio_20: '',
  cuota_convenio_15: '',
  activa: true,
})

const editingId = ref(null)
const saving = ref(false)
const totalManual = ref(false)

function toNumber(value) {
  if (value === '' || value === null || value === undefined) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

const sumaDesglose = computed(() => {
  const programatica = toNumber(form.cuota_programatica)
  const extraprogramatica = toNumber(form.cuota_extraprogramatica)
  if (programatica === null || extraprogramatica === null) return null
  return Math.round((programatica + extraprogramatica) * 100) / 100
})

const desgloseIncompleto = computed(
  () => toNumber(form.cuota_programatica) === null || toNumber(form.cuota_extraprogramatica) === null,
)

const totalDescuadrado = computed(() => {
  const total = toNumber(form.cuota_total)
  const suma = sumaDesglose.value
  if (total === null || suma === null) return false
  return Math.abs(total - suma) > 0.001
})

// Mientras el total no se cargue a mano sigue al desglose. El flag lo activa el
// propio input del total, asi no hay que adivinar de donde viene el cambio.
watch(sumaDesglose, (suma) => {
  if (totalManual.value) return
  form.cuota_total = suma === null ? '' : String(suma)
})

function requestClose() {
  if (!saving.value) emit('close')
}

function resetForm() {
  Object.assign(form, {
    nombre: '',
    tipo: 'carrera',
    sucursal: sucursales.value[0]?.id || '',
    duracion: '',
    descripcion: '',
    plan_cuotas: '',
    importe_matricula: '',
    cuota_programatica: '',
    cuota_extraprogramatica: '',
    cuota_total: '',
    cuota_convenio_20: '',
    cuota_convenio_15: '',
    activa: true,
  })
  editingId.value = null
  totalManual.value = false
}

watch(
  () => [props.open, props.carrera],
  ([isOpen, carrera]) => {
    if (!isOpen) return
    if (carrera) {
      editingId.value = carrera.id
      Object.assign(form, {
        nombre: carrera.nombre ?? '',
        tipo: carrera.tipo ?? 'carrera',
        sucursal: carrera.sucursal ?? '',
        duracion: carrera.duracion ?? '',
        descripcion: carrera.descripcion ?? '',
        plan_cuotas: carrera.plan_cuotas ?? '',
        importe_matricula: carrera.importe_matricula ?? '',
        cuota_programatica: carrera.cuota_programatica ?? '',
        cuota_extraprogramatica: carrera.cuota_extraprogramatica ?? '',
        cuota_total: carrera.cuota_total ?? '',
        cuota_convenio_20: carrera.cuota_convenio_20 ?? '',
        cuota_convenio_15: carrera.cuota_convenio_15 ?? '',
        activa: Boolean(carrera.activa),
      })
      // Si el total guardado no es la suma del desglose se respeta el valor
      // guardado y deja de recalcularse al tocar las partes.
      totalManual.value = true
    } else {
      resetForm()
    }
  },
  { immediate: true },
)

function optionalNumber(value) {
  const parsed = toNumber(value)
  return parsed === null ? null : parsed
}

async function handleSubmit() {
  saving.value = true
  try {
    const payload = {
      nombre: form.nombre,
      tipo: form.tipo,
      sucursal: form.sucursal,
      duracion: form.duracion,
      descripcion: form.descripcion,
      plan_cuotas: optionalNumber(form.plan_cuotas),
      importe_matricula: optionalNumber(form.importe_matricula),
      cuota_programatica: optionalNumber(form.cuota_programatica),
      cuota_extraprogramatica: optionalNumber(form.cuota_extraprogramatica),
      cuota_total: optionalNumber(form.cuota_total),
      cuota_convenio_20: optionalNumber(form.cuota_convenio_20),
      cuota_convenio_15: optionalNumber(form.cuota_convenio_15),
      activa: form.activa,
    }
    const saved = editingId.value
      ? await updateCarrera(editingId.value, payload)
      : await createCarrera(payload)
    toast.success(editingId.value ? 'Carrera actualizada' : 'Carrera creada')
    emit('saved', saved)
    emit('close')
  } catch (err) {
    toast.error(err.message || 'No se pudo guardar la carrera.')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.form-intro,
.field-help {
  display: block;
  color: var(--text-secondary);
  font-size: 0.78rem;
  line-height: 1.35;
}

.field-help {
  margin-top: 5px;
}

.field-help-block {
  margin: 0 0 12px;
}

.field-warning {
  margin: 12px 0 0;
  padding: 8px 10px;
  border-radius: 0.6rem;
  background: #fff7ed;
  color: #9a3412;
  font-size: 0.8rem;
}

.checkbox-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  color: var(--text-secondary);
}
</style>