<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="$emit('close')">
      <form class="modal-card" @submit.prevent="handleSubmit">
        <header class="modal-head">
          <div>
            <p class="eyebrow">{{ editingId ? 'Edicion de alumno' : 'Alta de alumno' }}</p>
            <h2>{{ editingId ? 'Editar alumno' : 'Nuevo alumno' }}</h2>
            <span>
              {{ editingId ? 'Actualiza los datos administrativos del alumno seleccionado.' : 'Datos administrativos iniciales para operar en el CRM.' }}
            </span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar" @click="$emit('close')">×</button>
        </header>

        <section class="modal-section">
          <h3>Identificacion</h3>
          <div class="modal-grid">
            <label>Legajo<input v-model="form.legajo" required /></label>
            <label>DNI<input v-model="form.dni" required /></label>
            <label>Nombre<input v-model="form.nombre" required /></label>
            <label>Apellido<input v-model="form.apellido" required /></label>
          </div>
        </section>

        <section class="modal-section">
          <h3>Contacto y cursada</h3>
          <div class="modal-grid">
            <label>Email<input v-model="form.email" type="email" /></label>
            <label>Telefono<input v-model="form.telefono" /></label>
            <label>
              Sucursal
              <select v-model="form.sucursal" required>
                <option v-for="s in sucursales" :key="s.id" :value="s.id">{{ s.nombre }}</option>
              </select>
            </label>
            <label>
              Carrera
              <select v-model="form.carrera">
                <option value="">Sin asignar</option>
                <option v-for="c in carreras" :key="c.id" :value="c.id">{{ c.nombre }}</option>
              </select>
            </label>
          </div>
        </section>

        <footer class="modal-actions">
          <button class="secondary-button" type="button" @click="$emit('close')">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="saving" type="submit">
            {{ saving ? 'Guardando...' : editingId ? 'Guardar cambios' : 'Guardar alumno' }}
          </button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { useAlumnos } from '@/composables/useAlumnos'
import { useCatalogos } from '@/composables/useCatalogos'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  open: { type: Boolean, default: false },
  alumno: { type: Object, default: null },
})

const emit = defineEmits(['close', 'saved'])

const { createAlumno, updateAlumno } = useAlumnos()
const { sucursales, carreras } = useCatalogos()
const toast = useToast()

const form = reactive({
  legajo: '',
  nombre: '',
  apellido: '',
  dni: '',
  email: '',
  telefono: '',
  sucursal: '',
  carrera: '',
})

const editingId = ref(null)
const saving = ref(false)

function resetForm() {
  Object.assign(form, {
    legajo: '',
    nombre: '',
    apellido: '',
    dni: '',
    email: '',
    telefono: '',
    sucursal: sucursales.value[0]?.id || '',
    carrera: '',
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
        carrera: alumno.carrera || '',
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
    const payload = { ...form, carrera: form.carrera || null }
    const saved = editingId.value
      ? await updateAlumno(editingId.value, payload)
      : await createAlumno(payload)
    toast.success(editingId.value ? 'Alumno actualizado' : 'Alumno creado')
    emit('saved', saved)
    emit('close')
  } catch (err) {
    toast.error(err.message || 'No se pudo guardar el alumno.')
  } finally {
    saving.value = false
  }
}
</script>
