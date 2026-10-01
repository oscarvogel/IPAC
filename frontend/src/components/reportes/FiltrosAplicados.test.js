import { mount } from '@vue/test-utils'
import { describe, expect, it, vi, afterEach } from 'vitest'
import ReporteFiltros from './ReporteFiltros.vue'
afterEach(() => vi.useRealTimers())
describe('filtros aplicados y edición pendiente', () => {
  const filtros = { desde: '2026-09-01', hasta: '2026-09-30', sucursal: 1, medio: 'efectivo', usuario: '' }
  function create() { return mount(ReporteFiltros, { props: { filtros, sucursales: [{ id: 1, nombre: 'Posadas' }] } }) }
  it('las etiquetas describen la consulta aplicada y exportar no aplica el borrador', async () => {
    const wrapper = create()
    await wrapper.findAll('input')[0].setValue('2026-08-01')
    expect(wrapper.text()).toContain('Cambios pendientes')
    expect(wrapper.get('.report-filter-chips').text()).not.toContain('01/08/2026')
    await wrapper.get('.reports-export-action').trigger('click')
    expect(wrapper.emitted('aplicar')).toBeUndefined()
    await wrapper.get('.reports-apply-action').trigger('click')
    expect(wrapper.emitted('aplicar')[0][1]).toBe('personalizado')
  })
  it('los atajos y quitar etiquetas consultan directamente usando lo aplicado', async () => {
    vi.useFakeTimers(); vi.setSystemTime(new Date(2026, 9, 6))
    const wrapper = create()
    await wrapper.findAll('input')[0].setValue('2025-01-01')
    await wrapper.findAll('.report-filter-shortcuts button')[0].trigger('click')
    expect(wrapper.emitted('aplicar')[0]).toEqual([{ ...filtros, desde: '2026-10-06', hasta: '2026-10-06' }, 'hoy'])
    await wrapper.findAll('.report-filter-chips button').find(button => button.text().startsWith('Medio:')).trigger('click')
    expect(wrapper.emitted('aplicar')[1][0]).toEqual({ ...filtros, medio: '' })
    await wrapper.findAll('.report-filter-shortcuts button')[2].trigger('click')
    expect(wrapper.emitted('aplicar')[2]).toEqual([{ desde: '', hasta: '', medio: '', sucursal: '', usuario: '' }, 'todos'])
  })
})
