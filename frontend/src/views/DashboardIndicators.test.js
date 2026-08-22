import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'
import DashboardView from './DashboardView.vue'

vi.mock('@/composables/useAuth', async () => {
  const { ref } = await import('vue')
  return { useAuth: () => ({ user: ref({ perfil: { sucursal: { id: 1, nombre: 'Posadas' } } }), can: () => true }) }
})

vi.mock('@/composables/useCaja', async () => {
  const { ref } = await import('vue')
  return {
    useCaja: () => ({
      cajaHoy: ref(null),
      cajaMovimientos: ref([]),
      error: ref(''),
      loadCajaHoy: vi.fn(async () => {}),
    }),
  }
})

vi.mock('@/composables/useCatalogos', async () => {
  const { ref } = await import('vue')
  return {
    useCatalogos: () => ({
      sucursales: ref([{ id: 1, nombre: 'Posadas' }]),
      loadCatalogos: vi.fn(async () => {}),
    }),
  }
})

vi.mock('@/composables/useDashboardFilters', async () => {
  const { ref } = await import('vue')
  return { useDashboardFilters: () => ({ selectedSucursalId: ref('1') }) }
})

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ error: vi.fn() }),
}))

vi.mock('@/lib/api', () => ({
  apiRequest: vi.fn(async (path) => {
    if (path === '/alumnos/') return { count: 12 }
    if (path === '/pagos/') return { results: [] }
    return {
      cobranzas: { total: 25000, hoy: 5000, cantidad_pagos: 2, por_medio: {} },
      cuenta_corriente: { deuda: 18000, saldo_a_favor: 0, alumnos_con_deuda: 3, cuotas_vencidas: 2 },
      cajas: { abiertas: 1, cerradas: 0, diferencia_acumulada: 0 },
    }
  }),
  getToken: vi.fn(),
  setToken: vi.fn(),
}))

describe('indicadores móviles del Dashboard', () => {
  it('prioriza cuatro métricas y ofrece un control expandible accesible', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: ['/dashboard', '/alumnos', '/caja', '/reportes', '/deudores', '/configuracion']
        .map((path) => ({ path, component: { template: '<div />' } })),
    })
    await router.push('/dashboard')
    await router.isReady()
    const wrapper = mount(DashboardView, { global: { plugins: [router] } })
    await flushPromises()

    const primaryLabels = wrapper.findAll('.stat-card:not(.stat-card-secondary) .stat-label').map((item) => item.text())
    expect(primaryLabels).toEqual(['Alumnos', 'Cobrado del mes', 'Cobrado hoy', 'Deuda pendiente'])
    expect(wrapper.findAll('.stat-action').length).toBeGreaterThanOrEqual(4)
    expect(wrapper.get('.stat-action').text()).toContain('Ver alumnos')

    const toggle = wrapper.get('.dashboard-stats-toggle')
    expect(toggle.attributes('aria-controls')).toBe('dashboard-indicators')
    expect(toggle.attributes('aria-expanded')).toBe('false')
    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('true')
    expect(wrapper.get('#dashboard-indicators').classes()).toContain('show-all-mobile-stats')
  })
})
