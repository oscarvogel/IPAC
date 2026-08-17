<template>
  <aside class="sidebar bg-primary text-primary-soft">
    <div class="brand-block">
      <img src="/logo-ipac.jpg" alt="IPAC" class="brand-logo" />
      <div class="brand-copy">
        <p class="brand">IPAC</p>
        <small>CRM administrativo</small>
      </div>
      <button
        class="sidebar-close"
        type="button"
        aria-label="Cerrar navegación"
        @click="$emit('close')"
      >
        <XMarkIcon aria-hidden="true" />
      </button>
    </div>

    <nav class="main-nav" aria-label="Módulos">
      <router-link
        v-for="module in modules"
        :key="module.to"
        :to="module.to"
        class="nav-link"
        active-class="active"
        @click="$emit('close')"
      >
        <component :is="module.icon" class="nav-icon" aria-hidden="true" />
        <span class="nav-copy">
          <span>{{ module.label }}</span>
          <small>{{ module.meta }}</small>
        </span>
      </router-link>
    </nav>

    <div ref="userArea" class="sidebar-footer">
      <div class="sidebar-user">
        <span class="sidebar-avatar">
          <UserIcon aria-hidden="true" />
        </span>
        <span class="sidebar-user-copy">
          <small>{{ user?.perfil?.sucursal?.nombre || 'Sin sucursal' }}</small>
          <strong>{{ user?.username || 'Invitado' }}</strong>
        </span>
        <button
          class="sidebar-user-menu"
          type="button"
          aria-label="Ver información de la sesión"
          aria-controls="sidebar-session-menu"
          :aria-expanded="userMenuOpen"
          @click="userMenuOpen = !userMenuOpen"
        >
          <EllipsisVerticalIcon aria-hidden="true" />
        </button>
      </div>

      <Transition name="session-menu">
        <section
          v-if="userMenuOpen"
          id="sidebar-session-menu"
          class="sidebar-session-menu"
          role="region"
          aria-label="Detalles de la sesión"
        >
          <dl>
            <div>
              <dt><ShieldCheckIcon aria-hidden="true" /> Rol</dt>
              <dd>{{ currentRoleLabel }}</dd>
            </div>
            <div>
              <dt><BuildingStorefrontIcon aria-hidden="true" /> Sucursal</dt>
              <dd>{{ user?.perfil?.sucursal?.nombre || 'Sin asignar' }}</dd>
            </div>
            <div>
              <dt><GlobeAltIcon aria-hidden="true" /> Alcance</dt>
              <dd>{{ user?.perfil?.puede_ver_todas_las_sucursales ? 'Todas las sedes' : 'Sede asignada' }}</dd>
            </div>
          </dl>

          <button v-if="canManageUsers" type="button" class="session-manage-users" @click="openUsers">
            <Cog6ToothIcon aria-hidden="true" />
            <span>Gestionar usuarios</span>
            <ArrowRightIcon aria-hidden="true" />
          </button>
        </section>
      </Transition>

      <div class="sidebar-footer-divider" />
      <button type="button" class="logout-button" @click="handleLogout">
        <ArrowRightOnRectangleIcon aria-hidden="true" />
        <span>Salir</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowRightIcon,
  ArrowRightOnRectangleIcon,
  BuildingOffice2Icon,
  BuildingStorefrontIcon,
  ChartBarSquareIcon,
  Cog6ToothIcon,
  DocumentArrowUpIcon,
  EllipsisVerticalIcon,
  GlobeAltIcon,
  HomeIcon,
  ShieldCheckIcon,
  TagIcon,
  UserGroupIcon,
  UserIcon,
  WalletIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { useAuth } from '@/composables/useAuth'

defineEmits(['close'])

const router = useRouter()
const route = useRoute()
const { user, logout } = useAuth()
const userArea = ref(null)
const userMenuOpen = ref(false)

const canManageUsers = computed(() => {
  const rol = user.value?.perfil?.rol
  return rol === 'superadmin' || rol === 'administracion'
})

const currentRoleLabel = computed(() => {
  const labels = {
    superadmin: 'Superadmin',
    administracion: 'Administración',
    tesoreria: 'Tesorería',
    caja: 'Caja',
    consulta: 'Consulta',
  }
  return labels[user.value?.perfil?.rol] || 'Sin rol'
})

const modules = computed(() => {
  const base = [
    { to: '/dashboard', label: 'Dashboard', meta: 'Resumen', icon: HomeIcon },
    { to: '/alumnos', label: 'Alumnos', meta: 'CRM', icon: UserGroupIcon },
    { to: '/caja', label: 'Caja', meta: 'Tesorería', icon: WalletIcon },
    { to: '/conceptos', label: 'Conceptos', meta: 'Aranceles', icon: TagIcon },
    { to: '/reportes', label: 'Reportes', meta: 'Listados', icon: ChartBarSquareIcon },
    { to: '/sucursales', label: 'Sucursales', meta: 'Accesos', icon: BuildingOffice2Icon },
  ]
  if (canManageUsers.value) {
    base.push({ to: '/usuarios', label: 'Usuarios', meta: 'Permisos', icon: UserIcon })
    base.push({ to: '/importaciones', label: 'Cargar datos', meta: 'Plantillas', icon: DocumentArrowUpIcon })
  }
  return base
})

function handleLogout() {
  userMenuOpen.value = false
  logout()
  router.replace('/login')
}

function openUsers() {
  userMenuOpen.value = false
  router.push('/usuarios')
}

function handleDocumentPointerDown(event) {
  if (!userMenuOpen.value || userArea.value?.contains(event.target)) return
  userMenuOpen.value = false
}

function handleDocumentKeydown(event) {
  if (event.key === 'Escape') userMenuOpen.value = false
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
  document.addEventListener('keydown', handleDocumentKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
  document.removeEventListener('keydown', handleDocumentKeydown)
})

watch(
  () => route.path,
  () => {
    userMenuOpen.value = false
  },
)
</script>
