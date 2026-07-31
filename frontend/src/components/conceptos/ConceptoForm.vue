<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="$emit('close')">
      <form class="modal-card" @submit.prevent="handleSubmit">
        <header class="modal-head">
          <div>
            <p class="eyebrow">
              {{ editingId ? 'Edición de concepto' : 'Alta de concepto' }}
            </p>
            <h2>{{ editingId ? 'Editar concepto' : 'Nuevo concepto cobrable' }}</h2>
            <span>
              {{
                editingId
                  ? 'Actualiza el concepto cobrable seleccionado.'
                  : 'Carga un nuevo concepto para asociar a pagos y cuotas.'
              }}
            </span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar" @click="$emit('close')">
            <XMarkIcon aria-hidden="true" />
          </button>
        </header>

        <section class="modal-section">
          <h3>Datos del concepto</h3>
          <div class="modal-grid">
            <label>
              Nombre
              <input v-model="form.nombre" required maxlength="160" />
            </label>
            <label>
              Tipo
              <select v-model="form.tipo" required>
                <option value="matricula">Matrícula</option>
                <option value="cuota">Cuota</option>
                <option value="material">Material</option>
                <option value="otro">Otro</option>
              </select>
            </label>
            <label>
              Importe
              <input
                v-model="form.importe"
                type="number"
                min="0"
                step="0.01"
                required
              />
            </label>
            <label>
              Sucursal
              <select v-model="form.sucursal" required>
                <option v-for="s in sucursales" :key="s.id" :value="s.id">
                  {{ s.nombre }}
                </option>
              </select>
            </label>
            <label>
              Carrera
              <select v-model="form.carrera">
                <option value="">Aplica a todas</option>
                <option
                  v-for="c in carrerasFiltradas"
                  :key="c.id"
                  :value="c.id"
                >
                  {{ c.nombre }}
                </option>
              </select>
            </label>
            <label v-if="editingId" class="checkbox-inline">
              <input v-model="form.activo" type="checkbox" />
              Concepto activo
            </label>
          </div>
        </section>

        <footer class="modal-actions">
          <button class="secondary-button" type="button" @click="$emit('close')">
            Cancelar
          </button>
          <button class="primary-button modal-submit" :disabled="saving" type="submit">
            {{ saving ? 'Guardando...' : editingId ? 'Guardar cambios' : 'Crear concepto' }}
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
import { useConceptos } from '@/composables/useConceptos'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  open: { type: Boolean, default: false },
  concepto: { type: Object, default: null },
})

const emit = defineEmits(['close', 'saved'])

const { createConcepto, updateConcepto } = useConceptos()
const { sucursales, carreras } = useCatalogos()
const toast = useToast()

const form = reactive({
  nombre: '',
  tipo: 'cuota',
  importe: '',
  sucursal: '',
  carrera: '',
  activo: true,
})

const editingId = ref(null)
const saving = ref(false)

const carrerasFiltradas = computed(() => {
  if (!form.sucursal) return []
  return carreras.value.filter((c) => String(c.sucursal) === String(form.sucursal))
})

function resetForm() {
  Object.assign(form, {
    nombre: '',
    tipo: 'cuota',
    importe: '',
    sucursal: sucursales.value[0]?.id || '',
    carrera: '',
    activo: true,
  })
  editingId.value = null
}

watch(
  () => [props.open, props.concepto],
  ([isOpen, concepto]) => {
    if (!isOpen) return
    if (concepto) {
      editingId.value = concepto.id
      Object.assign(form, {
        nombre: concepto.nombre,
        tipo: concepto.tipo,
        importe: concepto.importe,
        sucursal: concepto.sucursal,
        carrera: concepto.carrera || '',
        activo: Boolean(concepto.activo),
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
    const payload = {
      nombre: form.nombre,
      tipo: form.tipo,
      importe: form.importe,
      sucursal: form.sucursal,
      carrera: form.carrera || null,
      activo: form.activo,
    }
    const saved = editingId.value
      ? await updateConcepto(editingId.value, payload)
      : await createConcepto(payload)
    toast.success(editingId.value ? 'Concepto actualizado' : 'Concepto creado')
    emit('saved', saved)
    emit('close')
  } catch (err) {
    toast.error(err.message || 'No se pudo guardar el concepto.')
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
  color: var(--text-secondary);
}
</style>
