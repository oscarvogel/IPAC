<template>
  <section class="users-workspace text-text-primary">
    <AppPageState
      v-if="!pageReady"
      :loading="!pageError"
      :error="pageError"
      label="los usuarios"
      @retry="loadPage"
    />
    <template v-else>
    <div class="users-metrics-grid cash-metrics-grid">
      <article
        v-for="stat in stats"
        :key="stat.label"
        class="users-metric-card cash-metric-card border-border bg-surface"
      >
        <span class="cash-metric-icon" :class="`cash-metric-icon-${stat.tone}`">
          <component :is="stat.icon" aria-hidden="true" />
        </span>
        <span class="cash-metric-copy">
          <span>{{ stat.label }}</span>
          <strong>{{ stat.value }}</strong>
          <small>{{ stat.detail }}</small>
        </span>
      </article>
    </div>

    <section class="users-toolbar border-border bg-surface" aria-label="Filtros de usuarios">
      <div class="users-toolbar-heading">
        <span class="users-toolbar-icon">
          <UserGroupIcon aria-hidden="true" />
        </span>
        <div>
          <p class="eyebrow">Accesos y permisos</p>
          <h2>Directorio de usuarios</h2>
          <p>Administrá perfiles, roles y alcance por sucursal.</p>
        </div>
      </div>

      <div class="users-filters">
        <label class="users-search-field">
          <MagnifyingGlassIcon aria-hidden="true" />
          <span class="sr-only">Buscar usuario</span>
          <input v-model="searchQuery" type="search" placeholder="Buscar usuario o email" />
        </label>

        <label class="users-select-field">
          <BuildingStorefrontIcon aria-hidden="true" />
          <span class="sr-only">Filtrar por sucursal</span>
          <select v-model="sucursalFilter">
            <option value="todas">Todas las sucursales</option>
            <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
              {{ sucursal.nombre }}
            </option>
          </select>
          <ChevronDownIcon aria-hidden="true" />
        </label>

        <label class="users-select-field users-role-filter">
          <ShieldCheckIcon aria-hidden="true" />
          <span class="sr-only">Filtrar por rol</span>
          <select v-model="rolFilter">
            <option value="">Todos los roles</option>
            <option value="superadmin">Superadmin</option>
            <option value="administracion">Administración</option>
            <option value="tesoreria">Tesorería</option>
            <option value="caja">Caja</option>
            <option value="consulta">Consulta</option>
          </select>
          <ChevronDownIcon aria-hidden="true" />
        </label>

        <label class="users-active-filter" :class="{ active: onlyActive }">
          <input v-model="onlyActive" class="sr-only" type="checkbox" />
          <CheckIcon aria-hidden="true" />
          <span>Solo activos</span>
        </label>

        <button
          v-if="canManageUsers"
          type="button"
          class="users-primary-action bg-primary hover:bg-primary-hover"
          @click="openNewUsuarioForm"
        >
          <UserPlusIcon aria-hidden="true" />
          <span>Nuevo usuario</span>
        </button>
      </div>
    </section>

    <UsuarioList
      :usuarios="filteredUsuarios"
      :filtered="hasActiveFilters"
      :can-edit="canManageUsers"
      :can-deactivate="canManageUsers"
      :can-manage-superadmins="auth.role.value === 'superadmin'"
      @edit="openEditForm"
      @deactivate="requestDeactivate"
    />

    <UsuarioForm
      :open="showUsuarioForm"
      :usuario="editingUsuario"
      :sucursales="sucursales"
      @close="closeUsuarioForm"
      @saved="onUsuarioSaved"
    />

    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  BuildingStorefrontIcon,
  CheckCircleIcon,
  CheckIcon,
  ChevronDownIcon,
  GlobeAltIcon,
  KeyIcon,
  MagnifyingGlassIcon,
  ShieldCheckIcon,
  UserGroupIcon,
  UserPlusIcon,
} from '@heroicons/vue/24/outline'
import { useUsuarios } from '@/composables/useUsuarios'
import { useCatalogos } from '@/composables/useCatalogos'
import { useToast } from '@/composables/useToast'
import { useAuth } from '@/composables/useAuth'
import { confirmSensitiveUserChange } from '@/lib/swal'
import UsuarioForm from '@/components/usuarios/UsuarioForm.vue'
import UsuarioList from '@/components/usuarios/UsuarioList.vue'
import AppPageState from '@/components/ui/AppPageState.vue'

const { sucursales, loadCatalogos } = useCatalogos()
const { usuarios, error: usuariosError, loadUsuarios, deactivateUsuario } = useUsuarios()
const toast = useToast()
const auth = useAuth()
const canManageUsers = computed(() => auth.can('manage-users'))

const searchQuery = ref('')
const sucursalFilter = ref('todas')
const rolFilter = ref('')
const onlyActive = ref(false)

const showUsuarioForm = ref(false)
const editingUsuario = ref(null)
const pageReady = ref(false)
const pageError = ref('')

onMounted(loadPage)

async function loadPage() {
  pageReady.value = false
  pageError.value = ''
  try {
    await Promise.all([loadCatalogos(), loadUsuarios()])
    if (usuariosError.value) throw new Error(usuariosError.value)
    pageReady.value = true
  } catch (err) {
    pageError.value = err.message || 'No se pudo cargar el directorio de usuarios.'
  }
}

const branchUsuarios = computed(() => {
  if (sucursalFilter.value === 'todas') return usuarios.value
  return usuarios.value.filter(
    (usuario) => String(usuario.perfil?.sucursal?.id) === String(sucursalFilter.value),
  )
})

const filteredUsuarios = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase('es')
  return branchUsuarios.value.filter((usuario) => {
    if (onlyActive.value && !usuario.is_active) return false
    if (rolFilter.value && usuario.perfil?.rol !== rolFilter.value) return false
    const searchable = [
      usuario.username,
      usuario.first_name,
      usuario.last_name,
      usuario.email,
      usuario.perfil?.sucursal?.nombre,
    ]
      .filter(Boolean)
      .join(' ')
      .toLocaleLowerCase('es')
    return !query || searchable.includes(query)
  })
})

const hasActiveFilters = computed(() => Boolean(
  searchQuery.value.trim()
  || sucursalFilter.value !== 'todas'
  || rolFilter.value
  || onlyActive.value,
))

const activeCount = computed(
  () => branchUsuarios.value.filter((usuario) => usuario.is_active).length,
)

const rolesCount = computed(
  () => new Set(branchUsuarios.value.map((usuario) => usuario.perfil?.rol).filter(Boolean)).size,
)

const globalAccessCount = computed(
  () => branchUsuarios.value.filter(
    (usuario) => usuario.perfil?.puede_ver_todas_las_sucursales,
  ).length,
)

const selectedBranchName = computed(() => {
  if (sucursalFilter.value === 'todas') return 'en toda la institución'
  const branch = sucursales.value.find(
    (sucursal) => String(sucursal.id) === String(sucursalFilter.value),
  )
  return branch ? `en ${branch.nombre}` : 'en la sucursal seleccionada'
})

const stats = computed(() => [
  {
    label: 'Total de usuarios',
    value: branchUsuarios.value.length,
    detail: selectedBranchName.value,
    tone: 'primary',
    icon: UserGroupIcon,
  },
  {
    label: 'Usuarios activos',
    value: activeCount.value,
    detail: `${branchUsuarios.value.length - activeCount.value} inactivos`,
    tone: 'success',
    icon: CheckCircleIcon,
  },
  {
    label: 'Roles asignados',
    value: rolesCount.value,
    detail: 'niveles de permisos en uso',
    tone: 'warning',
    icon: KeyIcon,
  },
  {
    label: 'Acceso global',
    value: globalAccessCount.value,
    detail: 'usuarios con todas las sedes',
    tone: 'info',
    icon: GlobeAltIcon,
  },
])

function openNewUsuarioForm() {
  if (!canManageUsers.value) return
  editingUsuario.value = null
  showUsuarioForm.value = true
}

function openEditForm(usuario) {
  if (!canManageUsers.value) return
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

async function requestDeactivate(usuario) {
  if (!canManageUsers.value) return
  const confirmation = await confirmSensitiveUserChange({
    title: 'Desactivar usuario',
    userName: usuario.username,
    description: 'Perderá el acceso al sistema hasta que vuelva a ser activado. Su historial permanecerá sin cambios.',
    beforeRole: usuario.perfil?.rol,
  })
  if (!confirmation.isConfirmed) return
  try {
    await deactivateUsuario(usuario.id)
    toast.success('Usuario desactivado')
  } catch (err) {
    toast.error(err.message || 'No se pudo desactivar el usuario.')
  }
}
</script>
