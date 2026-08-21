import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'
import AppSidebar from './AppSidebar.vue'

describe('navegación lateral', () => {
  it('usa filas completas como enlaces sin indicadores de submenú', async () => {
    const routes = [
      '/dashboard',
      '/alumnos',
      '/deudores',
      '/caja',
      '/reportes',
    ].map((path) => ({
      path,
      component: { template: '<div />' },
    }))
    const router = createRouter({ history: createMemoryHistory(), routes })
    await router.push('/dashboard')
    await router.isReady()

    const wrapper = mount(AppSidebar, { global: { plugins: [router] } })

    expect(wrapper.find('.nav-chevron').exists()).toBe(false)
    expect(wrapper.findAll('.main-nav a')).toHaveLength(5)

    await wrapper.get('a[href="/alumnos"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/alumnos')
  })
  it('abre el detalle de la sesión y permite cerrarlo con Escape', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/dashboard', component: { template: '<div />' } },
        { path: '/:pathMatch(.*)*', component: { template: '<div />' } },
      ],
    })
    await router.push('/dashboard')
    await router.isReady()

    const wrapper = mount(AppSidebar, {
      attachTo: document.body,
      global: { plugins: [router] },
    })
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
