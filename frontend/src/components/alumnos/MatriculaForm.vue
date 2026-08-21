<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="requestClose">
      <form
        v-focus-trap="{ close: requestClose, busy: saving }"
        v-form-validation
        class="modal-card compact-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="matricula-form-title"
        :aria-busy="saving"
        @submit.prevent="handleSubmit"
      >
        <header class="modal-head">
          <div>
            <p class="eyebrow">Trayectoria académica</p>
            <h2 id="matricula-form-title">{{ changeCareer ? 'Cambiar carrera' : editing ? 'Editar matrícula' : 'Nueva matrícula' }}</h2>
            <span v-if="alumno">{{ alumno.apellido }}, {{ alumno.nombre }}</span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar formulario" @click="requestClose">
            <XMarkIcon aria-hidden="true" />
          </button>
        </header>

        <section class="modal-section">
          <div class="modal-grid">
            <label v-if="!editing || changeCareer">
              Carrera/curso
              <select v-model="form.carrera" required>
                <option value="">Seleccioná una carrera</option>
                <option v-for="carrera in selectableCareers" :key="carrera.id" :value="carrera.id">
                  {{ carrera.nombre }}
                </option>
              </select>
            </label>
            <label v-else>
              Carrera/curso
              <input :value="matricula?.carrera_nombre || 'Sin carrera'" disabled />
            </label>
            <label>
              Fecha de inicio
              <input v-model="form.fecha_inicio" type="date" required />
            </label>
            <label class="matricula-observation-field">
              Observación
              <textarea v-model="form.observacion" rows="3" placeholder="Detalle opcional" />
            </label>
          </div>
          <p class="matricula-form-help">
            {{ changeCareer
              ? 'La matrícula actual se finalizará y se creará una nueva, conservando todo el historial.'
              : editing
              ? 'La matrícula permanece activa. Para cerrarla, usá la acción «Finalizar» desde el historial.'
              : 'Se creará como matrícula activa. Para cerrarla, usá la acción «Finalizar» desde el historial.' }}
          </p>
        </section>

        <footer class="modal-actions">
          <button class="secondary-button" type="button" :disabled="saving" @click="requestClose">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="saving" type="submit">
            {{ changeCareer ? 'Confirmar cambio' : editing ? 'Guardar cambios' : 'Crear matrícula' }}
          </button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import { useCatalogos } from '@/composables/useCatalogos'
import { useMatriculas } from '@/composables/useMatriculas'
import { useToast } from '@/composables/useToast'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'

const props = defineProps({
  open: { type: Boolean, default: false },
  alumno: { type: Object, default: null },
  matricula: { type: Object, default: null },
  changeCareer: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'saved'])
const { carreras } = useCatalogos()
const { createMatricula, updateMatricula, cambiarCarrera } = useMatriculas()
const toast = useToast()

const form = reactive({ carrera: '', fecha_inicio: '', observacion: '' })
const saving = ref(false)
const editing = computed(() => Boolean(props.matricula))
const availableCareers = computed(() => carreras.value.filter((carrera) => (
  String(carrera.sucursal) === String(props.alumno?.sucursal)
)))
const selectableCareers = computed(() => availableCareers.value.filter((carrera) => (
  !props.changeCareer || String(carrera.id) !== String(props.matricula?.carrera)
)))

function today() {
  return new Date().toISOString().slice(0, 10)
}

function resetForm() {
  Object.assign(form, {
    carrera: props.changeCareer ? '' : (props.matricula?.carrera || ''),
    fecha_inicio: props.matricula?.fecha_inicio || today(),
    observacion: props.matricula?.observacion || '',
  })
}

function requestClose() {
  if (!saving.value) emit('close')
}

watch(() => [props.open, props.matricula?.id, props.alumno?.id], ([isOpen]) => {
  if (isOpen) resetForm()
}, { immediate: true })

async function handleSubmit() {
  if (!props.alumno) return
  saving.value = true
  try {
    const payload = {
      fecha_inicio: form.fecha_inicio,
      observacion: form.observacion,
    }
    const saved = props.changeCareer
      ? await cambiarCarrera(props.matricula.id, { ...payload, carrera: form.carrera })
      : editing.value
      ? await updateMatricula(props.matricula.id, payload)
      : await createMatricula({
        ...payload,
        fecha_fin: null,
        alumno: props.alumno.id,
        carrera: form.carrera,
        estado: 'activa',
      })
    toast.success(props.changeCareer ? 'Carrera actualizada y trayectoria conservada' : editing.value ? 'Matrícula actualizada' : 'Matrícula creada')
    emit('saved', saved)
    emit('close')
  } catch (err) {
    toast.error(err.message || 'No se pudo guardar la matrícula.')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.matricula-observation-field {
  grid-column: 1 / -1;
}

.matricula-observation-field textarea {
  width: 100%;
  resize: vertical;
}

.matricula-form-help {
  margin: .9rem 0 0;
  color: var(--text-secondary, #64748b);
  font-size: .82rem;
  line-height: 1.4;
}
</style>
