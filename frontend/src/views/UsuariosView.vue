<template>
  <section class="users-screen">
    <div class="stats-grid">
      <article v-for="stat in stats" :key="stat.label" class="stat-card">
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
        <small>{{ stat.detail }}</small>
      </article>
    </div>

    <div class="topbar-filters">
      <input
        v-model="searchQuery"
        class="global-search"
        placeholder="Buscar usuario..."
      />
      <select v-model="sucursalFilter" class="compact-select">
        <option value="todas">Todas las sucursales</option>
        <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
          {{ sucursal.nombre }}
        </option>
      </select>
      <select v-model="rolFilter" class="compact-select">
        <option value="">Todos los roles</option>
        <option value="superadmin">Superadmin</option>
        <option value="administracion">Administracion</option>
        <option value="tesoreria">Tesoreria</option>
        <option value="caja">Caja</option>
        <option value="consulta">Consulta</option>
      </select>
      <button type="button" class="primary-button" @click="openNewUsuarioForm">Nuevo usuario</button>
    </div>

    <div class="panel table-card">
      <div class="panel-head">
        <div>
          <h2>Usuarios del sistema</h2>
          <p>{{ filteredUsuarios.length }} usuarios visibles</p>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Nombre</th>
            <th>Email</th>
            <th>Rol</th>
            <th>Sucursal</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="usuario in filteredUsuarios" :key="usuario.id">
            <td><strong>{{ usuario.username }}</strong></td>
            <td>{{ [usuario.first_name, usuario.last_name].filter(Boolean).join(' ') || '—' }}</td>
            <td>{{ usuario.email || '—' }}</td>
            <td><span class="table-badge">{{ rolLabel(usuario) }}</span></td>
            <td>{{ usuario.perfil?.sucursal?.nombre || '—' }}</td>
            <td>
              <span :class="'estado-badge ' + (usuario.is_active ? 'activo' : 'inactivo')">
                {{ usuario.is_active ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="table-actions">
              <button class="secondary-button" type="button" @click="openEditForm(usuario)">
                Editar
              </button>
              <button
                v-if="usuario.is_active"
                class="danger-button"
                type="button"
                @click="confirmDeactivate(usuario)"
              >
                Desactivar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!filteredUsuarios.length" class="empty-state flat">
        No hay usuarios para el filtro actual.
      </p>
    </div>

    <UsuarioForm
      :open="showUsuarioForm"
      :usuario="editingUsuario"
      :sucursales="sucursales"
      @close="closeUsuarioForm"
      @saved="onUsuarioSaved"
    />
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useUsuarios } from '@/composables/useUsuarios'
import { useCatalogos } from '@/composables/useCatalogos'
import { useToast } from '@/composables/useToast'
import UsuarioForm from '@/components/usuarios/UsuarioForm.vue'

const { sucursales, loadCatalogos } = useCatalogos()
const { usuarios, loadUsuarios, deactivateUsuario } = useUsuarios()
const toast = useToast()

const searchQuery = ref('')
const sucursalFilter = ref('todas')
const rolFilter = ref('')

const showUsuarioForm = ref(false)
const editingUsuario = ref(null)

onMounted(async () => {
  await Promise.all([loadCatalogos(), loadUsuarios()])
})

const filteredUsuarios = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return usuarios.value.filter((usuario) => {
    const matchesSucursal =
      sucursalFilter.value === 'todas' ||
      String(usuario.perfil?.sucursal?.id) === String(sucursalFilter.value)
    const matchesRol = !rolFilter.value || usuario.perfil?.rol === rolFilter.value
    const text = [
      usuario.username,
      usuario.first_name,
      usuario.last_name,
      usuario.email,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    const matchesQuery = !query || text.includes(query)
    return matchesSucursal && matchesRol && matchesQuery
  })
})

const stats = computed(() => [
  { label: 'Usuarios activos', value: usuarios.value.filter((u) => u.is_active).length, detail: `de ${usuarios.value.length} total` },
  { label: 'Sucursales', value: sucursales.value.length, detail: 'Posadas y Eldorado' },
  { label: 'Roles', value: new Set(usuarios.value.map((u) => u.perfil?.rol)).size, detail: 'distintos' },
  { label: 'Superadmin', value: usuarios.value.filter((u) => u.perfil?.rol === 'superadmin').length, detail: 'acceso completo' },
])

function rolLabel(usuario) {
  const map = { superadmin: 'Superadmin', administracion: 'Admin', tesoreria: 'Tesorería', caja: 'Caja', consulta: 'Consulta' }
  return map[usuario.perfil?.rol] || usuario.perfil?.rol || '—'
}

function openNewUsuarioForm() {
  editingUsuario.value = null
  showUsuarioForm.value = true
}

function openEditForm(usuario) {
  editingUsuario.value = usuario
  showUsuarioForm.value = true
}

function closeUsuarioForm() {
  showUsuarioForm.value = false
  editingUsuario.value = null
}

function onUsuarioSaved() {
  closeUsuarioForm()
}

async function confirmDeactivate(usuario) {
  try {
    await deactivateUsuario(usuario.id)
    toast.success('Usuario desactivado')
  } catch (err) {
    toast.error(err.message || 'No se pudo desactivar el usuario.')
  }
}
</script>

<style scoped>
</style>
