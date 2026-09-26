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

  it('agrupa los filtros avanzados e indica cuántos están activos', async () => {
    const wrapper = shallowMount(DeudoresView)
    await flushPromises()

    const moreFilters = wrapper.get('.debtors-more-filters')
    expect(moreFilters.attributes('aria-expanded')).toBe('false')
    expect(moreFilters.text()).toContain('0')
    expect(wrapper.find('[aria-label="Filtrar por carrera"]').exists()).toBe(false)

    await moreFilters.trigger('click')
    expect(wrapper.get('.debtors-more-filters').attributes('aria-expanded')).toBe('true')
    expect(wrapper.find('[aria-label="Filtrar por carrera"]').exists()).toBe(true)

    await wrapper.get('[aria-label="Deuda desde"]').setValue('1000')
    await wrapper.get('[aria-label="Mes correspondiente"]').setValue('09-2026')
    expect(wrapper.get('.debtors-more-filters').text()).toContain('2')

    await wrapper.get('.debtors-clear-advanced').trigger('click')
    expect(wrapper.get('[aria-label="Deuda desde"]').element.value).toBe('')
    expect(wrapper.get('[aria-label="Mes correspondiente"]').element.value).toBe('')
    expect(wrapper.get('.debtors-more-filters').text()).toContain('0')
  })
})
