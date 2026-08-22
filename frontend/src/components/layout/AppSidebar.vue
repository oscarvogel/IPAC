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
      <div
        v-for="module in modules"
        :key="module.id"
        class="nav-module"
        :class="{ 'nav-module-active': isModuleActive(module) }"
      >
        <div class="nav-module-row" :class="{ 'nav-module-row-single': !hasSubmenu(module) }">
          <router-link
            :to="module.to"
            class="nav-link"
            :class="{ active: isModuleActive(module) }"
            @click="closeNavigation"
          >
            <component :is="module.icon" class="nav-icon" aria-hidden="true" />
            <span class="nav-copy">
              <span>{{ module.label }}</span>
              <small>{{ module.meta }}</small>
            </span>
          </router-link>
          <button
            v-if="hasSubmenu(module)"
            type="button"
            class="nav-submenu-toggle"
            :aria-label="`${isExpanded(module) ? 'Contraer' : 'Expandir'} opciones de ${module.label}`"
            :aria-expanded="isExpanded(module)"
            :aria-controls="`nav-submenu-${module.id}`"
            @click="toggleModule(module.id)"
          >
            <ChevronDownIcon aria-hidden="true" />
          </button>
        </div>

        <ul
          v-if="hasSubmenu(module) && isExpanded(module)"
          :id="`nav-submenu-${module.id}`"
          class="nav-submenu"
        >
          <li v-for="child in module.children" :key="child.id">
            <router-link
              :to="child.to"
              :class="{ active: isChildActive(child) }"
              @click="closeNavigation"
            >
              {{ child.label }}
            </router-link>
          </li>
        </ul>
      </div>
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
  BanknotesIcon,
  BuildingStorefrontIcon,
  ChartBarSquareIcon,
  ChevronDownIcon,
  Cog6ToothIcon,
  EllipsisVerticalIcon,
  GlobeAltIcon,
  HomeIcon,
  ShieldCheckIcon,
  UserGroupIcon,
  UserIcon,
  WalletIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { useAuth } from '@/composables/useAuth'

const emit = defineEmits(['close'])

const router = useRouter()
const route = useRoute()
const auth = useAuth()
const { user, logout } = auth
const userArea = ref(null)
const userMenuOpen = ref(false)
const expandedModule = ref(null)

const canManageUsers = computed(() => auth.can('manage-users'))

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
    { id: 'dashboard', to: '/dashboard', label: 'Dashboard', meta: 'Resumen', icon: HomeIcon },
    {
      id: 'alumnos',
      to: '/alumnos',
      label: 'Alumnos',
      meta: 'CRM',
      icon: UserGroupIcon,
      children: [
        { id: 'alumnos-directorio', label: 'Directorio', to: '/alumnos' },
        ...(auth.can('manage-alumnos')
          ? [{ id: 'alumnos-nuevo', label: 'Nuevo alumno', to: { path: '/alumnos', query: { accion: 'nuevo' } } }]
          : []),
        ...(auth.can('manage-fees')
          ? [{ id: 'alumnos-cuotas', label: 'Generar cuotas masivas', to: { path: '/alumnos', query: { accion: 'cuotas-masivas' } } }]
          : []),
      ],
    },
    { id: 'deudores', to: '/deudores', label: 'Deudores', meta: 'Cobranzas', icon: BanknotesIcon },
    {
      id: 'caja',
      to: '/caja',
      label: 'Caja',
      meta: 'Tesorería',
      icon: WalletIcon,
      children: [
        { id: 'caja-dia', label: 'Caja del día', to: '/caja' },
        ...(auth.can('operate-cash')
          ? [
              { id: 'caja-ingreso', label: 'Ingreso manual', to: { path: '/caja', query: { accion: 'ingreso' } } },
              { id: 'caja-egreso', label: 'Egreso manual', to: { path: '/caja', query: { accion: 'egreso' } } },
              { id: 'caja-retiro', label: 'Retiro de efectivo', to: { path: '/caja', query: { accion: 'retiro' } } },
              { id: 'caja-cerrar', label: 'Cerrar caja', to: { path: '/caja', query: { accion: 'cerrar' } } },
            ]
          : []),
      ],
    },
    {
      id: 'reportes',
      to: { path: '/reportes', query: { seccion: 'resumen' } },
      label: 'Reportes',
      meta: 'Listados',
      icon: ChartBarSquareIcon,
      children: [
        { id: 'reportes-resumen', label: 'Resumen', to: { path: '/reportes', query: { seccion: 'resumen' } } },
        { id: 'reportes-cobranzas', label: 'Cobranzas', to: { path: '/reportes', query: { seccion: 'cobranzas' } } },
        { id: 'reportes-morosidad', label: 'Morosidad', to: { path: '/reportes', query: { seccion: 'morosidad' } } },
        { id: 'reportes-caja', label: 'Caja', to: { path: '/reportes', query: { seccion: 'caja' } } },
        { id: 'reportes-alumnos', label: 'Alumnos', to: { path: '/reportes', query: { seccion: 'alumnos' } } },
      ],
    },
  ]
  if (canManageUsers.value) {
    base.push({
      id: 'configuracion',
      to: '/configuracion',
      label: 'Configuración',
      meta: 'Catálogos y accesos',
      icon: Cog6ToothIcon,
      children: [
        { id: 'configuracion-sucursales', label: 'Sucursales', to: '/sucursales' },
        { id: 'configuracion-conceptos', label: 'Conceptos cobrables', to: '/conceptos' },
        { id: 'configuracion-ajustes', label: 'Descuentos y recargos', to: '/ajustes-cuotas' },
        { id: 'configuracion-usuarios', label: 'Usuarios y permisos', to: '/usuarios' },
        { id: 'configuracion-importaciones', label: 'Importar datos', to: '/importaciones' },
        { id: 'configuracion-auditoria', label: 'Auditoría', to: '/auditoria' },
      ],
    })
  }
  return base
})

function routePath(target) {
  return typeof target === 'string' ? target : target.path
}

function hasSubmenu(module) {
  return (module.children?.length || 0) > 1
}

function isModuleActive(module) {
  return route.path === routePath(module.to)
    || module.children?.some((child) => route.path === routePath(child.to))
}

function isChildActive(child) {
  if (route.path !== routePath(child.to)) return false
  if (typeof child.to === 'string' || !child.to.query) return !route.query.accion && !route.query.seccion
  if (child.to.query.seccion === 'resumen' && !route.query.seccion) return true
  return Object.entries(child.to.query).every(([key, value]) => route.query[key] === value)
}

function isExpanded(module) {
  return expandedModule.value === module.id
}

function toggleModule(moduleId) {
  expandedModule.value = expandedModule.value === moduleId ? null : moduleId
  userMenuOpen.value = false
}

function closeNavigation() {
  emit('close')
}

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
  if (event.key !== 'Escape') return
  userMenuOpen.value = false
  expandedModule.value = null
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
  () => [route.path, route.query.accion, route.query.seccion],
  () => {
    userMenuOpen.value = false
    const activeModule = modules.value.find((module) => hasSubmenu(module) && isModuleActive(module))
    expandedModule.value = activeModule?.id || null
  },
  { immediate: true },
)
</script>
