import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'
import AppTopbar from './AppTopbar.vue'

vi.mock('@/composables/useAuth', async () => {
  const { ref } = await import('vue')
  const user = ref({ perfil: { sucursal: { id: 1, nombre: 'Posadas' } } })
  return { useAuth: () => ({ user }) }
})

vi.mock('@/composables/useCatalogos', async () => {
  const { ref } = await import('vue')
  return {
    useCatalogos: () => ({ sucursales: ref([]), loadCatalogos: vi.fn() }),
  }
})

vi.mock('@/composables/useDashboardFilters', async () => {
  const { ref } = await import('vue')
  return { useDashboardFilters: () => ({ selectedSucursalId: ref('') }) }
})

vi.mock('@/composables/useTopbarActions', async () => {
  const { ref } = await import('vue')
  return { useTopbarActions: () => ({ actions: ref([]) }) }
})

vi.mock('@/composables/useTheme', async () => {
  const { ref } = await import('vue')
  return {
    useTheme: () => ({ isDark: ref(false), toggleTheme: vi.fn() }),
  }
})

async function mountTopbar(path = '/dashboard', meta = {}) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/dashboard', component: { template: '<div />' } },
      { path: '/ajustes-cuotas', meta, component: { template: '<div />' } },
    ],
  })
  await router.push(path)
  await router.isReady()
  return mount(AppTopbar, { attachTo: document.body, global: { plugins: [router] } })
}

describe('estado accesible del menu mobile', () => {
  it('expone controles ARIA y devuelve el foco al cerrar', async () => {
    const wrapper = await mountTopbar()
    const menuButton = wrapper.get('.mobile-menu-button')

    expect(menuButton.attributes('aria-controls')).toBe('app-sidebar')
    expect(menuButton.attributes('aria-expanded')).toBe('false')
    expect(menuButton.attributes('aria-label')).toBe('Abrir navegación')

    await wrapper.setProps({ sidebarOpen: true })
    expect(menuButton.attributes('aria-expanded')).toBe('true')
    expect(menuButton.attributes('aria-label')).toBe('Cerrar navegación')

    await wrapper.setProps({ sidebarOpen: false })
    await nextTick()
    await nextTick()
    expect(document.activeElement).toBe(menuButton.element)
    wrapper.unmount()
  })

  it('oculta el encabezado global cuando la vista tiene encabezado contextual', async () => {
    const wrapper = await mountTopbar('/ajustes-cuotas', { hideTopbarHeading: true })

    expect(wrapper.find('.topbar-heading').exists()).toBe(false)
    expect(wrapper.classes()).toContain('topbar--contextual')
    wrapper.unmount()
  })
})
