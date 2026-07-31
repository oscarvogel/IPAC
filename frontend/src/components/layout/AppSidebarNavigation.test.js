import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it } from 'vitest'
import AppSidebar from './AppSidebar.vue'

describe('navegación lateral', () => {
  it('usa filas completas como enlaces sin indicadores de submenú', async () => {
    const routes = [
      '/dashboard',
      '/alumnos',
      '/caja',
      '/conceptos',
      '/reportes',
      '/sucursales',
    ].map((path) => ({
      path,
      component: { template: '<div />' },
    }))
    const router = createRouter({ history: createMemoryHistory(), routes })
    await router.push('/dashboard')
    await router.isReady()

    const wrapper = mount(AppSidebar, { global: { plugins: [router] } })

    expect(wrapper.find('.nav-chevron').exists()).toBe(false)
    expect(wrapper.findAll('.main-nav a')).toHaveLength(6)

    await wrapper.get('a[href="/alumnos"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/alumnos')
  })
})
