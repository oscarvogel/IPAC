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
