import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { nextTick } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AppSidebar from './AppSidebar.vue'

const authState = vi.hoisted(() => ({ role: 'administracion' }))

vi.mock('@/composables/useAuth', async () => {
  const { computed } = await import('vue')
  const capabilities = {
    administracion: ['manage-users', 'manage-alumnos', 'manage-fees', 'operate-cash'],
    consulta: [],
  }
  return {
    useAuth: () => ({
      user: computed(() => ({
        username: 'admin',
        perfil: { rol: authState.role, sucursal: { nombre: 'Posadas' } },
      })),
      can: (capability) => capabilities[authState.role]?.includes(capability) || false,
      logout: vi.fn(),
    }),
  }
})

function buildRouter(path = '/dashboard') {
  const paths = [
    '/dashboard', '/alumnos', '/deudores', '/caja', '/reportes', '/configuracion',
    '/sucursales', '/conceptos', '/ajustes-cuotas', '/usuarios', '/importaciones', '/auditoria', '/login',
  ]
  const router = createRouter({
    history: createMemoryHistory(),
    routes: paths.map((routePath) => ({ path: routePath, component: { template: '<div />' } })),
  })
  return router.push(path).then(() => router.isReady()).then(() => router)
}

describe('navegación lateral contextual', () => {
  beforeEach(() => {
    authState.role = 'administracion'
  })

  it('expande un único módulo, expone su estado y cierra con Escape', async () => {
    const router = await buildRouter('/dashboard')
    const wrapper = mount(AppSidebar, { attachTo: document.body, global: { plugins: [router] } })

    const alumnosToggle = wrapper.get('[aria-controls="nav-submenu-alumnos"]')
    expect(alumnosToggle.attributes('aria-expanded')).toBe('false')
    await alumnosToggle.trigger('click')
    expect(alumnosToggle.attributes('aria-expanded')).toBe('true')
    expect(wrapper.get('#nav-submenu-alumnos').text()).toContain('Generar cuotas masivas')

    const cajaToggle = wrapper.get('[aria-controls="nav-submenu-caja"]')
    await cajaToggle.trigger('click')
    expect(cajaToggle.attributes('aria-expanded')).toBe('true')
    expect(wrapper.find('#nav-submenu-alumnos').exists()).toBe(false)

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await nextTick()
    expect(wrapper.find('#nav-submenu-caja').exists()).toBe(false)
    wrapper.unmount()
  })

  it('abre automáticamente el módulo activo y cierra el drawer al elegir una acción', async () => {
    const router = await buildRouter('/alumnos?accion=cuotas-masivas')
    const wrapper = mount(AppSidebar, { global: { plugins: [router] } })

    expect(wrapper.get('[aria-controls="nav-submenu-alumnos"]').attributes('aria-expanded')).toBe('true')
    expect(wrapper.get('a[href="/alumnos?accion=cuotas-masivas"]').classes()).toContain('active')

    await wrapper.get('a[href="/alumnos?accion=nuevo"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.query.accion).toBe('nuevo')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('oculta mutaciones para consulta y evita desplegables redundantes', async () => {
    authState.role = 'consulta'
    const router = await buildRouter('/alumnos')
    const wrapper = mount(AppSidebar, { global: { plugins: [router] } })

    expect(wrapper.find('[aria-controls="nav-submenu-alumnos"]').exists()).toBe(false)
    expect(wrapper.find('[aria-controls="nav-submenu-caja"]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Nuevo alumno')
    expect(wrapper.text()).not.toContain('Ingreso manual')
    expect(wrapper.text()).not.toContain('Configuración')
    expect(wrapper.find('[aria-controls="nav-submenu-reportes"]').exists()).toBe(true)
  })

  it('mantiene el detalle de sesión accesible y lo cierra con Escape', async () => {
    const router = await buildRouter('/dashboard')
    const wrapper = mount(AppSidebar, { attachTo: document.body, global: { plugins: [router] } })
    const menuButton = wrapper.get('.sidebar-user-menu')

    expect(menuButton.attributes('aria-expanded')).toBe('false')
    await menuButton.trigger('click')
    expect(menuButton.attributes('aria-expanded')).toBe('true')
    expect(wrapper.get('#sidebar-session-menu').attributes('role')).toBe('region')

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await nextTick()
    expect(wrapper.find('#sidebar-session-menu').exists()).toBe(false)
    wrapper.unmount()
  })
})
