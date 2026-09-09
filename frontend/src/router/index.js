import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/lib/api'
import AppShell from '@/components/layout/AppShell.vue'
import LoginView from '@/views/LoginView.vue'
import PlaceholderView from '@/views/PlaceholderView.vue'
import AccessDeniedView from '@/views/AccessDeniedView.vue'
import { canViewRoute } from '@/lib/permissions'
import { useAuth } from '@/composables/useAuth'

const DashboardView = () => import('@/views/DashboardView.vue')
const AlumnosView = () => import('@/views/AlumnosView.vue')
const DeudoresView = () => import('@/views/DeudoresView.vue')
const CajaView = () => import('@/views/CajaView.vue')
const ConceptosView = () => import('@/views/ConceptosView.vue')
const ReportesView = () => import('@/views/ReportesView.vue')
const SucursalesView = () => import('@/views/SucursalesView.vue')
const UsuariosView = () => import('@/views/UsuariosView.vue')
const ConfiguracionView = () => import('@/views/ConfiguracionView.vue')
const ImportacionesView = () => import('@/views/ImportacionesView.vue')
const AuditoriaView = () => import('@/views/AuditoriaView.vue')
const AjustesCuotasView = () => import('@/views/AjustesCuotasView.vue')

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
