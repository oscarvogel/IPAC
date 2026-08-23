import { flushPromises, shallowMount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import DeudoresView from './DeudoresView.vue'

vi.mock('@/composables/useCatalogos', async () => {
  const { ref } = await import('vue')
  return {
    useCatalogos: () => ({
      sucursales: ref([]),
      carreras: ref([]),
      conceptos: ref([]),
      loadCatalogos: vi.fn(async () => {}),
    }),
  }
})

vi.mock('@/composables/useDeudores', async () => {
  const { ref } = await import('vue')
  return {
    useDeudores: () => ({
      deudores: ref([]),
      pagination: ref({ count: 0, page: 1, pageSize: 10 }),
      loading: ref(false),
      error: ref(''),
      loadDeudores: vi.fn(async () => {}),
    }),
  }
})

vi.mock('@/composables/useAuth', () => ({
  useAuth: () => ({ can: () => false }),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('@/composables/useReportes', () => ({
  useReportes: () => ({ exportarExcel: vi.fn() }),
}))

describe('estados vacíos de Deudores', () => {
  it('distingue una cartera vacía de filtros sin coincidencias', async () => {
    const wrapper = shallowMount(DeudoresView)
    await flushPromises()

    expect(wrapper.get('.debtors-empty').text()).toContain('No hay alumnos con deuda')

    await wrapper.get('input[type="search"]').setValue('alumno inexistente')
    expect(wrapper.get('.debtors-empty').text()).toContain('No hay resultados para estos filtros')
  })
})
