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

    <div class="sidebar-footer">
      <div class="sidebar-user">
        <span class="sidebar-avatar">
          <UserIcon aria-hidden="true" />
        </span>
        <span class="sidebar-user-copy">
          <small>{{ user?.perfil?.sucursal?.nombre || 'Sin sucursal' }}</small>
          <strong>{{ user?.username || 'Invitado' }}</strong>
        </span>
        <EllipsisVerticalIcon class="sidebar-user-menu" aria-hidden="true" />
      </div>
      <div class="sidebar-footer-divider" />
      <button type="button" class="logout-button" @click="handleLogout">
        <ArrowRightOnRectangleIcon aria-hidden="true" />
        <span>Salir</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRightOnRectangleIcon,
  BuildingOffice2Icon,
  ChartBarSquareIcon,
  EllipsisVerticalIcon,
  HomeIcon,
  TagIcon,
  UserGroupIcon,
  UserIcon,
  WalletIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { useAuth } from '@/composables/useAuth'

defineEmits(['close'])

const router = useRouter()
const { user, logout } = useAuth()

const canManageUsers = computed(() => {
  const rol = user.value?.perfil?.rol
  return rol === 'superadmin' || rol === 'administracion'
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
  }
  return base
})

function handleLogout() {
  logout()
  router.replace('/login')
}
</script>
