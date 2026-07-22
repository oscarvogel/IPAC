import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/lib/api'
import AppShell from '@/components/layout/AppShell.vue'
import LoginView from '@/views/LoginView.vue'
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
      { path: '', redirect: '/alumnos' },
      {
        path: 'alumnos',
        name: 'alumnos',
        component: PlaceholderView,
        props: {
          title: 'Alumnos',
          note: 'Modulo real llega en el PR 4 (extract alumnos module).',
        },
      },
      {
        path: 'caja',
        name: 'caja',
        component: PlaceholderView,
        props: {
          title: 'Caja',
          note: 'Modulo real llega en el PR 5 (extract caja module).',
        },
      },
      {
        path: 'conceptos',
        name: 'conceptos',
        component: PlaceholderView,
        props: {
          title: 'Conceptos',
          note: 'Modulo real llega en el PR 6 (extract conceptos module).',
        },
      },
      {
        path: 'reportes',
        name: 'reportes',
        component: PlaceholderView,
        props: {
          title: 'Reportes',
          note: 'Modulo real llega en el PR 7 (extract reportes module).',
        },
      },
      {
        path: 'sucursales',
        name: 'sucursales',
        component: PlaceholderView,
        props: {
          title: 'Sucursales',
          note: 'Modulo real llega en el PR 8 (extract sucursales module + dashboard).',
        },
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
    return next({ path: '/alumnos' })
  }
  return next()
})
