<template>
  <section class="users-workspace text-text-primary">
    <div class="users-metrics-grid cash-metrics-grid">
      <article
        v-for="(stat, index) in stats"
        :key="stat.label"
        class="users-metric-card cash-metric-card border-border bg-surface"
        :class="{ 'cash-metric-card-featured': index === 0 }"
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
      @edit="openEditForm"
      @deactivate="confirmDeactivate"
    />

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
import UsuarioForm from '@/components/usuarios/UsuarioForm.vue'
import UsuarioList from '@/components/usuarios/UsuarioList.vue'

const { sucursales, loadCatalogos } = useCatalogos()
const { usuarios, loadUsuarios, deactivateUsuario } = useUsuarios()
const toast = useToast()

const searchQuery = ref('')
const sucursalFilter = ref('todas')
const rolFilter = ref('')
const onlyActive = ref(false)

const showUsuarioForm = ref(false)
const editingUsuario = ref(null)

onMounted(async () => {
  await Promise.all([loadCatalogos(), loadUsuarios()])
})

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
