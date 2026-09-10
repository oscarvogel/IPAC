import { flushPromises, shallowMount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ReportesView from './ReportesView.vue'

const reportState = vi.hoisted(() => ({
  loadCatalogo: vi.fn(async () => {}),
  loadCatalogos: vi.fn(async () => {}),
  loadResumen: vi.fn(async () => {}),
  loadPagos: vi.fn(async () => {}),
  loadCobranzasUsuarios: vi.fn(async () => {}),
}))

vi.mock('@/composables/useCatalogos', async () => {
  const { ref } = await import('vue')
  return {
    useCatalogos: () => ({
      sucursales: ref([]),
      loadCatalogo: reportState.loadCatalogo,
      loadCatalogos: reportState.loadCatalogos,
    }),
  }
})

vi.mock('@/composables/useReportes', async () => {
  const { ref } = await import('vue')
  return {
    useReportes: () => ({
      resumen: ref({ cajas: {} }),
      pagos: ref([]),
      cobranzasUsuarios: ref([]),
      loading: ref(false),
      error: ref(''),
      loadResumen: reportState.loadResumen,
      loadPagos: reportState.loadPagos,
      loadCobranzasUsuarios: reportState.loadCobranzasUsuarios,
      exportarExcel: vi.fn(),
    }),
  }
})

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

async function mountReportes(path = '/reportes') {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/reportes', component: { template: '<div />' } }],
  })
  await router.push(path)
  await router.isReady()
  const wrapper = shallowMount(ReportesView, { global: { plugins: [router] } })
  await flushPromises()
  return wrapper
}

describe('carga progresiva de Reportes', () => {
  beforeEach(() => {
    Object.values(reportState).forEach((mock) => mock.mockClear())
  })

  it('carga solo el resumen al entrar en la pestaña Resumen', async () => {
    await mountReportes()

    expect(reportState.loadResumen).toHaveBeenCalledTimes(1)
    expect(reportState.loadPagos).not.toHaveBeenCalled()
    expect(reportState.loadCobranzasUsuarios).not.toHaveBeenCalled()
  })

  it('carga las tres fuentes necesarias al entrar directamente en Cobranzas', async () => {
    await mountReportes('/reportes?seccion=cobranzas')

    expect(reportState.loadResumen).toHaveBeenCalledTimes(1)
    expect(reportState.loadPagos).toHaveBeenCalledTimes(1)
    expect(reportState.loadCobranzasUsuarios).toHaveBeenCalledTimes(1)
  })

  it('difiere Cobranzas hasta seleccionar la pestaña y reutiliza el resumen', async () => {
    const wrapper = await mountReportes()
    const cobranzasTab = wrapper.findAll('.reports-tabs button').find((button) => button.text() === 'Cobranzas')

    await cobranzasTab.trigger('click')
    await flushPromises()

    expect(reportState.loadResumen).toHaveBeenCalledTimes(1)
    expect(reportState.loadPagos).toHaveBeenCalledTimes(1)
    expect(reportState.loadCobranzasUsuarios).toHaveBeenCalledTimes(1)
  })
})
