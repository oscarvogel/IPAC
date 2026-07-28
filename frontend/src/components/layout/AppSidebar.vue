<template>
  <aside class="sidebar">
    <div class="brand-block">
      <img src="/logo-ipac.jpg" alt="IPAC" class="brand-logo" />
      <div>
        <p class="brand">IPAC</p>
        <small>CRM administrativo</small>
      </div>
    </div>

    <nav class="main-nav" aria-label="Modulos">
      <router-link
        v-for="module in modules"
        :key="module.to"
        :to="module.to"
        class="nav-link"
        active-class="active"
      >
        <span>{{ module.label }}</span>
        <small>{{ module.meta }}</small>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <small>{{ user?.perfil?.sucursal?.nombre || 'Sin sucursal' }}</small>
      <strong>{{ user?.username || 'Invitado' }}</strong>
      <button type="button" @click="handleLogout">Salir</button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { user, logout } = useAuth()

const canManageUsers = computed(() => {
  const rol = user.value?.perfil?.rol
  return rol === 'superadmin' || rol === 'administracion'
})

const modules = computed(() => {
  const base = [
    { to: '/dashboard', label: 'Dashboard', meta: 'Resumen' },
    { to: '/alumnos', label: 'Alumnos', meta: 'CRM' },
    { to: '/caja', label: 'Caja', meta: 'Tesoreria' },
    { to: '/conceptos', label: 'Conceptos', meta: 'Aranceles' },
    { to: '/reportes', label: 'Reportes', meta: 'Listados' },
    { to: '/sucursales', label: 'Sucursales', meta: 'Accesos' },
  ]
  if (canManageUsers.value) {
    base.push({ to: '/usuarios', label: 'Usuarios', meta: 'Permisos' })
  }
  return base
})

function handleLogout() {
  logout()
  router.replace('/login')
}
</script>
