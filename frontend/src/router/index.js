import { createRouter, createWebHistory } from 'vue-router'
import PlaceholderView from '@/views/PlaceholderView.vue'

// Todas las rutas de momento renderizan un PlaceholderView.
// PR 2+ ira reemplazando cada entrada por su view real.
const routes = [
  { path: '/', redirect: '/alumnos' },
  {
    path: '/login',
    name: 'login',
    component: PlaceholderView,
    props: {
      title: 'Login',
      note: 'El formulario real de login llega en el PR 2 (extract api + auth composable).',
    },
  },
  {
    path: '/alumnos',
    name: 'alumnos',
    component: PlaceholderView,
    props: {
      title: 'Alumnos',
      note: 'Modulo real llega en el PR 4 (extract alumnos module).',
    },
  },
  {
    path: '/caja',
    name: 'caja',
    component: PlaceholderView,
    props: {
      title: 'Caja',
      note: 'Modulo real llega en el PR 5 (extract caja module).',
    },
  },
  {
    path: '/conceptos',
    name: 'conceptos',
    component: PlaceholderView,
    props: {
      title: 'Conceptos',
      note: 'Modulo real llega en el PR 6 (extract conceptos module).',
    },
  },
  {
    path: '/reportes',
    name: 'reportes',
    component: PlaceholderView,
    props: {
      title: 'Reportes',
      note: 'Modulo real llega en el PR 7 (extract reportes module).',
    },
  },
  {
    path: '/sucursales',
    name: 'sucursales',
    component: PlaceholderView,
    props: {
      title: 'Sucursales',
      note: 'Modulo real llega en el PR 8 (extract sucursales module + dashboard).',
    },
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

// Guard de auth provisorio.
// En el PR 2 se reemplaza por el chequeo de useAuth.
const TOKEN_KEY = 'ipac_token'
const isAuthenticated = () => Boolean(localStorage.getItem(TOKEN_KEY))

router.beforeEach((to, from, next) => {
  if (to.path !== '/login' && !isAuthenticated()) {
    return next({ path: '/login' })
  }
  if (to.path === '/login' && isAuthenticated()) {
    return next({ path: '/alumnos' })
  }
  return next()
})
