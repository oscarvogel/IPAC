<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="$emit('close')">
      <form class="modal-card" @submit.prevent="handleSubmit">
        <header class="modal-head">
          <div>
            <p class="eyebrow">
              {{ editingId ? 'Edicion de sucursal' : 'Alta de sucursal' }}
            </p>
            <h2>{{ editingId ? 'Editar sucursal' : 'Nueva sucursal' }}</h2>
            <span>
              {{
                editingId
                  ? 'Actualiza el codigo o nombre de la sucursal seleccionada.'
                  : 'Carga una nueva sucursal para empezar a operar.'
              }}
            </span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar" @click="$emit('close')">×</button>
        </header>

        <section class="modal-section">
          <h3>Datos de la sucursal</h3>
          <div class="modal-grid">
            <label>
              Codigo
              <input
                v-model="form.codigo"
                required
                maxlength="10"
                :disabled="Boolean(editingId)"
              />
            </label>
            <label>
              Nombre
              <input v-model="form.nombre" required maxlength="100" />
            </label>
            <label v-if="editingId" class="checkbox-inline">
              <input v-model="form.activa" type="checkbox" />
              Sucursal activa
            </label>
          </div>
        </section>

        <footer class="modal-actions">
          <button class="secondary-button" type="button" @click="$emit('close')">
            Cancelar
          </button>
          <button class="primary-button modal-submit" :disabled="saving" type="submit">
            {{ saving ? 'Guardando...' : editingId ? 'Guardar cambios' : 'Crear sucursal' }}
          </button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { useSucursales } from '@/composables/useSucursales'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  open: { type: Boolean, default: false },
  sucursal: { type: Object, default: null },
})

const emit = defineEmits(['close', 'saved'])

const { createSucursal, updateSucursal } = useSucursales()
const toast = useToast()

const form = reactive({
  codigo: '',
  nombre: '',
  activa: true,
})

const editingId = ref(null)
const saving = ref(false)

function resetForm() {
  Object.assign(form, { codigo: '', nombre: '', activa: true })
  editingId.value = null
}

watch(
  () => [props.open, props.sucursal],
  ([isOpen, sucursal]) => {
    if (!isOpen) return
    if (sucursal) {
      editingId.value = sucursal.id
      Object.assign(form, {
        codigo: sucursal.codigo,
        nombre: sucursal.nombre,
        activa: Boolean(sucursal.activa),
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
    const payload = editingId.value
      ? { nombre: form.nombre, activa: form.activa }
      : { codigo: form.codigo, nombre: form.nombre, activa: form.activa }
    const saved = editingId.value
      ? await updateSucursal(editingId.value, payload)
      : await createSucursal(payload)
    toast.success(editingId.value ? 'Sucursal actualizada' : 'Sucursal creada')
    emit('saved', saved)
    emit('close')
  } catch (err) {
    toast.error(err.message || 'No se pudo guardar la sucursal.')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.checkbox-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  color: #4a4a55;
}
</style>
