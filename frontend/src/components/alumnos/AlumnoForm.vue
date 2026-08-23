<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="requestClose">
      <form
        v-focus-trap="{ close: requestClose, busy: saving }"
        v-form-validation
        class="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="alumno-form-title"
        :aria-busy="saving"
        @submit.prevent="handleSubmit"
      >
        <header class="modal-head">
          <div>
            <p class="eyebrow">{{ editingId ? 'Edicion de alumno' : 'Alta de alumno' }}</p>
            <h2 id="alumno-form-title">{{ editingId ? 'Editar alumno' : 'Nuevo alumno' }}</h2>
            <span>
              {{ editingId ? 'Actualiza los datos administrativos del alumno seleccionado.' : 'Datos administrativos iniciales para operar en el CRM.' }}
            </span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar formulario" @click="requestClose">
            <XMarkIcon aria-hidden="true" />
          </button>
        </header>

        <section class="modal-section">
          <h3>Identificacion</h3>
          <div class="modal-grid">
            <label>Legajo<input v-model="form.legajo" name="legajo" autocomplete="off" required /></label>
            <label>DNI<input v-model="form.dni" name="dni" inputmode="numeric" autocomplete="off" required /></label>
            <label>Nombre<input v-model="form.nombre" name="nombre" autocomplete="given-name" required /></label>
            <label>Apellido<input v-model="form.apellido" name="apellido" autocomplete="family-name" required /></label>
          </div>
        </section>

        <section class="modal-section">
          <h3>Contacto y administración</h3>
          <div class="modal-grid">
            <label>Email<input v-model="form.email" name="email" type="email" autocomplete="email" /></label>
            <label>Teléfono<input v-model="form.telefono" name="telefono" type="tel" inputmode="tel" autocomplete="tel" /></label>
            <label>
              Sucursal
              <select v-model="form.sucursal" required>
                <option v-for="s in sucursales" :key="s.id" :value="s.id">{{ s.nombre }}</option>
              </select>
            </label>
          </div>
          <p class="alumno-form-guidance">
            La carrera se asigna mediante una matrícula desde la ficha del alumno.
          </p>
        </section>

        <footer class="modal-actions">
          <button class="secondary-button" type="button" :disabled="saving" @click="requestClose">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="saving" type="submit">
            <AppButtonContent
              :loading="saving"
              :label="editingId ? 'Guardar cambios' : 'Guardar alumno'"
              loading-label="Guardando…"
            />
          </button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import { useAlumnos } from '@/composables/useAlumnos'
import { useCatalogos } from '@/composables/useCatalogos'
import { useToast } from '@/composables/useToast'
import AppButtonContent from '@/components/ui/AppButtonContent.vue'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'

const props = defineProps({
  open: { type: Boolean, default: false },
  alumno: { type: Object, default: null },
})

const emit = defineEmits(['close', 'saved'])

const { createAlumno, updateAlumno } = useAlumnos()
const { sucursales } = useCatalogos()
const toast = useToast()

const form = reactive({
  legajo: '',
  nombre: '',
  apellido: '',
  dni: '',
  email: '',
  telefono: '',
  sucursal: '',
})

const editingId = ref(null)
const saving = ref(false)

function requestClose() {
  if (!saving.value) emit('close')
}

function resetForm() {
  Object.assign(form, {
    legajo: '',
    nombre: '',
    apellido: '',
    dni: '',
    email: '',
    telefono: '',
    sucursal: sucursales.value[0]?.id || '',
  })
  editingId.value = null
}

watch(
  () => [props.open, props.alumno],
  ([isOpen, alumno]) => {
    if (!isOpen) return
    if (alumno) {
      editingId.value = alumno.id
      Object.assign(form, {
        legajo: alumno.legajo,
        nombre: alumno.nombre,
        apellido: alumno.apellido,
        dni: alumno.dni,
        email: alumno.email || '',
        telefono: alumno.telefono || '',
        sucursal: alumno.sucursal,
      })
    } else {
      resetForm()
    }
  },
  { immediate: true },
)

async function handleSubmit() {
  saving.value = true
  try {
    const payload = { ...form }
    const saved = editingId.value
      ? await updateAlumno(editingId.value, payload)
      : await createAlumno(payload)
    toast.success(editingId.value ? 'Alumno actualizado' : 'Alumno creado. Ahora podés registrar su matrícula desde la ficha.')
    emit('saved', saved)
    emit('close')
  } catch (err) {
    toast.error(err.message || 'No se pudo guardar el alumno.')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.alumno-form-guidance {
  margin-top: 12px;
  color: var(--text-secondary);
  font-size: 12px;
}
</style>
