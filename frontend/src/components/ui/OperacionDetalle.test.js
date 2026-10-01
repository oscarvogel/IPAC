import { mount, flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import OperacionDetalle from './OperacionDetalle.vue'
const getRecibo = vi.hoisted(() => vi.fn())
vi.mock('@/composables/usePagos', () => ({ usePagos: () => ({ getRecibo }) }))
describe('detalle de operación', () => {
  it('navega al recibo con un único diálogo y reintenta solo la lectura', async () => {
    getRecibo.mockRejectedValueOnce(new Error('No se pudo leer')).mockResolvedValueOnce({ numero: 'REC-5', pago: { importe: '200' }, aplicaciones: [] })
    const previousFocus = document.createElement('button')
    document.body.append(previousFocus)
    previousFocus.focus()
    const wrapper = mount(OperacionDetalle, { props: { operacion: { id: 1, pago: 5, tipo_label: 'Pago', importe: '200', medio: 'efectivo', usuario_nombre: 'Cajero QA' } }, global: { stubs: { Teleport: true } }, attachTo: document.body })
    await wrapper.findAll('button').find(button => button.text() === 'Ver recibo').trigger('click'); await flushPromises()
    expect(wrapper.text()).toContain('No se pudo leer')
    await wrapper.findAll('button').find(button => button.text() === 'Reintentar recibo').trigger('click'); await flushPromises()
    expect(wrapper.text()).toContain('REC-5')
    expect(wrapper.findAll('[role="dialog"]')).toHaveLength(1)
    await wrapper.findAll('button').find(button => button.text() === 'Volver al detalle').trigger('click')
    expect(wrapper.text()).toContain('Cajero QA')
    await wrapper.get('[role="dialog"]').trigger('keydown', { key: 'Escape' })
    expect(wrapper.emitted('close')).toHaveLength(1)
    wrapper.unmount()
    await new Promise((resolve) => requestAnimationFrame(resolve))
    expect(document.activeElement).toBe(previousFocus)
    previousFocus.remove()
  })
})
