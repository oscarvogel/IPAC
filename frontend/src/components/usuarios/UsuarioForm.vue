<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="$emit('close')">
      <form class="modal-card compact-modal" @submit.prevent="handleSubmit">
        <header class="modal-head">
          <div>
            <p class="eyebrow">{{ editingId ? 'Edición' : 'Alta' }} de usuario</p>
            <h2>{{ editingId ? 'Editar usuario' : 'Nuevo usuario' }}</h2>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar" @click="$emit('close')">
            <XMarkIcon aria-hidden="true" />
          </button>
        </header>

        <section class="modal-section">
          <div class="modal-grid">
            <label>
              Usuario
              <input v-model="form.username" required maxlength="150" />
            </label>
            <label>
              Contraseña
              <input v-model="form.password" type="password" :required="!editingId" :placeholder="editingId ? 'Dejar vacío para mantener' : ''" />
            </label>
            <label>
              Nombre
              <input v-model="form.first_name" />
            </label>
            <label>
              Apellido
              <input v-model="form.last_name" />
            </label>
            <label>
              Email
              <input v-model="form.email" type="email" />
            </label>
            <label>
              Rol
              <select v-model="form.rol" required>
                <option value="superadmin">Superadmin</option>
                <option value="administracion">Administración</option>
                <option value="tesoreria">Tesorería</option>
                <option value="caja">Caja</option>
                <option value="consulta">Consulta</option>
              </select>
            </label>
            <label>
              Sucursal
              <select v-model="form.sucursal" required>
                <option v-for="s in sucursales" :key="s.id" :value="s.id">
                  {{ s.nombre }}
                </option>
              </select>
            </label>
            <label class="checkbox-inline">
              <input v-model="form.puede_ver_todas_las_sucursales" type="checkbox" />
              Acceso a todas las sucursales
            </label>
            <label v-if="editingId" class="checkbox-inline">
              <input v-model="form.is_active" type="checkbox" />
              Usuario activo
            </label>
          </div>
        </section>

        <footer class="modal-actions">
          <button class="secondary-button" type="button" @click="$emit('close')">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="saving" type="submit">
            {{ saving ? 'Guardando...' : editingId ? 'Guardar cambios' : 'Crear usuario' }}
          </button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import { useUsuarios } from '@/composables/useUsuarios'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  open: { type: Boolean, default: false },
  usuario: { type: Object, default: null },
  sucursales: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'saved'])

const { createUsuario, updateUsuario } = useUsuarios()
const toast = useToast()

const form = reactive({
  username: '',
  password: '',
  first_name: '',
  last_name: '',
  email: '',
  rol: 'consulta',
  sucursal: '',
  puede_ver_todas_las_sucursales: false,
  is_active: true,
})

const editingId = ref(null)
const saving = ref(false)

function resetForm() {
  Object.assign(form, {
    username: '',
    password: '',
    first_name: '',
    last_name: '',
    email: '',
    rol: 'consulta',
    sucursal: props.sucursales[0]?.id || '',
    puede_ver_todas_las_sucursales: false,
    is_active: true,
  })
  editingId.value = null
}

watch(
  () => [props.open, props.usuario],
  ([isOpen, usuario]) => {
    if (!isOpen) return
    if (usuario) {
      editingId.value = usuario.id
      const perfil = usuario.perfil || {}
      Object.assign(form, {
        username: usuario.username,
        password: '',
        first_name: usuario.first_name || '',
        last_name: usuario.last_name || '',
        email: usuario.email || '',
        rol: perfil.rol || 'consulta',
        sucursal: perfil.sucursal?.id || '',
        puede_ver_todas_las_sucursales: perfil.puede_ver_todas_las_sucursales || false,
        is_active: usuario.is_active,
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
      username: form.username,
      first_name: form.first_name,
      last_name: form.last_name,
      email: form.email,
      rol: form.rol,
      sucursal: form.sucursal,
      puede_ver_todas_las_sucursales: form.puede_ver_todas_las_sucursales,
      is_active: form.is_active,
    }
    if (form.password) {
      payload.password = form.password
    }
    const saved = editingId.value
      ? await updateUsuario(editingId.value, payload)
      : await createUsuario(payload)
    toast.success(editingId.value ? 'Usuario actualizado' : 'Usuario creado')
    emit('saved', saved)
    emit('close')
  } catch (err) {
    toast.error(err.message || 'No se pudo guardar el usuario.')
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
