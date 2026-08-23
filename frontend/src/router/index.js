import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/lib/api'
import AppShell from '@/components/layout/AppShell.vue'
import LoginView from '@/views/LoginView.vue'
import AlumnosView from '@/views/AlumnosView.vue'
import DeudoresView from '@/views/DeudoresView.vue'
import CajaView from '@/views/CajaView.vue'
import ConceptosView from '@/views/ConceptosView.vue'
import DashboardView from '@/views/DashboardView.vue'
import ReportesView from '@/views/ReportesView.vue'
import SucursalesView from '@/views/SucursalesView.vue'
import UsuariosView from '@/views/UsuariosView.vue'
import PlaceholderView from '@/views/PlaceholderView.vue'
import ImportacionesView from '@/views/ImportacionesView.vue'
import AccessDeniedView from '@/views/AccessDeniedView.vue'
import ConfiguracionView from '@/views/ConfiguracionView.vue'
import AuditoriaView from '@/views/AuditoriaView.vue'
import AjustesCuotasView from '@/views/AjustesCuotasView.vue'
import { canViewRoute } from '@/lib/permissions'
import { useAuth } from '@/composables/useAuth'

// Las rutas autenticadas viven como children de la ruta padre "/",
// cuyo component es AppShell. Asi el shell envuelve automaticamente
// cada vista autenticada y LoginView queda fuera del shell (top-level).
const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
  },
  {
    path: '/',
    component: AppShell,
    children: [
      { path: '', redirect: '/dashboard' },
      {
        path: 'dashboard',
        name: 'dashboard',
        component: DashboardView,
        meta: { roles: ['superadmin', 'administracion', 'tesoreria', 'caja', 'consulta'] },
      },
      {
        path: 'alumnos',
        name: 'alumnos',
        component: AlumnosView,
        meta: { roles: ['superadmin', 'administracion', 'tesoreria', 'caja', 'consulta'] },
      },
      {
        path: 'deudores',
        name: 'deudores',
        component: DeudoresView,
        meta: { roles: ['superadmin', 'administracion', 'tesoreria', 'caja', 'consulta'] },
      },
      {
        path: 'caja',
        name: 'caja',
        component: CajaView,
        meta: { roles: ['superadmin', 'administracion', 'tesoreria', 'caja', 'consulta'] },
      },
      {
        path: 'conceptos',
        name: 'conceptos',
        component: ConceptosView,
        meta: { roles: ['superadmin', 'administracion', 'tesoreria', 'caja', 'consulta'] },
      },
      {
        path: 'reportes',
        name: 'reportes',
        component: ReportesView,
        meta: { roles: ['superadmin', 'administracion', 'tesoreria', 'caja', 'consulta'] },
      },
      {
        path: 'sucursales',
        name: 'sucursales',
        component: SucursalesView,
        meta: { roles: ['superadmin', 'administracion', 'tesoreria', 'caja', 'consulta'] },
      },
      {
        path: 'usuarios',
        name: 'usuarios',
        component: UsuariosView,
        meta: { roles: ['superadmin', 'administracion'] },
      },
      {
        path: 'configuracion',
        name: 'configuracion',
        component: ConfiguracionView,
        meta: { roles: ['superadmin', 'administracion'] },
      },
      {
        path: 'ajustes-cuotas',
        name: 'ajustes-cuotas',
        component: AjustesCuotasView,
        meta: { roles: ['superadmin', 'administracion'] },
      },
      {
        path: 'auditoria',
        name: 'auditoria',
        component: AuditoriaView,
        meta: { roles: ['superadmin', 'administracion'] },
      },
      {
        path: 'importaciones',
        name: 'importaciones',
        component: ImportacionesView,
        meta: { roles: ['superadmin', 'administracion'] },
      },
    ],
  },
  {
    path: '/access-denied',
    name: 'access-denied',
    component: AccessDeniedView,
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: PlaceholderView,
    props: {
      title: '404',
      note: 'La ruta solicitada no existe.',
    },
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Guard de auth. Lee el token directo de localStorage via lib/api
// (el guard corre fuera del contexto Vue, no puede usar useAuth).
router.beforeEach(async (to, from, next) => {
  const hasToken = Boolean(getToken())
  if (to.path !== '/login' && !hasToken) {
    return next({ path: '/login' })
  }
  if (to.path === '/login' && hasToken) {
    return next({ path: '/dashboard' })
  }
  if (hasToken && to.meta.roles) {
    const auth = useAuth()
    if (!auth.user.value) await auth.fetchCurrentUser()
    if (!canViewRoute(auth.user.value, to.meta.roles)) return next({ name: 'access-denied' })
  }
  return next()
})
