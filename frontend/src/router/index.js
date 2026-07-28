import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/lib/api'
import AppShell from '@/components/layout/AppShell.vue'
import LoginView from '@/views/LoginView.vue'
import AlumnosView from '@/views/AlumnosView.vue'
import CajaView from '@/views/CajaView.vue'
import ConceptosView from '@/views/ConceptosView.vue'
import DashboardView from '@/views/DashboardView.vue'
import ReportesView from '@/views/ReportesView.vue'
import SucursalesView from '@/views/SucursalesView.vue'
import UsuariosView from '@/views/UsuariosView.vue'
import PlaceholderView from '@/views/PlaceholderView.vue'

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
      },
      {
        path: 'alumnos',
        name: 'alumnos',
        component: AlumnosView,
      },
      {
        path: 'caja',
        name: 'caja',
        component: CajaView,
      },
      {
        path: 'conceptos',
        name: 'conceptos',
        component: ConceptosView,
      },
      {
        path: 'reportes',
        name: 'reportes',
        component: ReportesView,
      },
      {
        path: 'sucursales',
        name: 'sucursales',
        component: SucursalesView,
      },
      {
        path: 'usuarios',
        name: 'usuarios',
        component: UsuariosView,
      },
    ],
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
router.beforeEach((to, from, next) => {
  const hasToken = Boolean(getToken())
  if (to.path !== '/login' && !hasToken) {
    return next({ path: '/login' })
  }
  if (to.path === '/login' && hasToken) {
    return next({ path: '/dashboard' })
  }
  return next()
})
