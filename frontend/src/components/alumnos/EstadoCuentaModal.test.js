import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import EstadoCuentaModal from './EstadoCuentaModal.vue'

const getEstadoCuenta = vi.hoisted(() => vi.fn().mockResolvedValue({
  resumen: {
    total_cuotas: '1000.00',
    saldo_pendiente: '450.00',
    saldo_vencido: '100.00',
    saldo_por_vencer: '350.00',
    saldo_a_favor: '0.00',
    saldo_neto: '450.00',
  },
  cuotas: [],
  pagos: [],
}))

vi.mock('@/composables/usePagos', () => ({
  usePagos: () => ({ getEstadoCuenta, getRecibo: vi.fn(), anularPago: vi.fn() }),
}))
vi.mock('@/composables/useAuth', () => ({ useAuth: () => ({ can: () => false }) }))
vi.mock('@/composables/useToast', () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }))

describe('EstadoCuentaModal', () => {
  beforeEach(() => vi.clearAllMocks())

  it('conserva la cuenta y restaura el foco al cerrar el detalle con Escape', async () => {
    getEstadoCuenta.mockResolvedValueOnce({ resumen: { total_cuotas: '200', saldo_pendiente: '0', saldo_a_favor: '0' }, cuotas: [], pagos: [{ id: 4, importe: '200', fecha: '2026-09-30', medio: 'efectivo', numero_recibo: 'REC-4' }] })
    const wrapper = mount(EstadoCuentaModal, { props: { open: true, alumno: { id: 1 } }, attachTo: document.body, global: { stubs: { Teleport: true, AppModalTransition: { template: '<div><slot /></div>' } } } })
    await flushPromises()
    const trigger = wrapper.findAll('button').find(button => button.text() === 'Ver detalle')
    await trigger.trigger('click')
    expect(wrapper.getComponent({ name: 'OperacionDetalle' }).props('returnFocus')).toBe(trigger.element)
    const dialog = wrapper.get('.operation-panel')
    expect(dialog.text()).toContain('30/09/2026')
    expect(wrapper.get('.account-modal').isVisible()).toBe(false)
    await dialog.trigger('keydown', { key: 'Escape' }); await flushPromises()
    expect(wrapper.get('.account-modal').isVisible()).toBe(true)
    expect(document.activeElement).toBe(wrapper.get('[data-operacion-id="4"]').element)
    expect(getEstadoCuenta).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('explica por separado el saldo pendiente, vencido y por vencer', async () => {
    const wrapper = mount(EstadoCuentaModal, {
      props: { open: true, alumno: { id: 12, nombre: 'Alumna', apellido: 'Ficticia' } },
      global: {
        stubs: {
          Teleport: true,
          AppModalTransition: { template: '<div><slot /></div>' },
          ReciboPrintView: true,
        },
      },
    })
    await flushPromises()

    expect(getEstadoCuenta).toHaveBeenCalledWith(12)
    expect(wrapper.text()).toContain('Saldo pendiente')
    expect(wrapper.text()).toContain('Saldo vencido')
    expect(wrapper.text()).toContain('Saldo por vencer')
    expect(wrapper.text()).toContain('$ 100')
    expect(wrapper.text()).toContain('$ 350')
  })
})
