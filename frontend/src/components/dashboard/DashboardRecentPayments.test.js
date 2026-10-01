import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import DashboardRecentPayments from './DashboardRecentPayments.vue'

const getRecibo = vi.hoisted(() => vi.fn())
vi.mock('@/composables/usePagos', () => ({ usePagos: () => ({ getRecibo }) }))

describe('últimos pagos del dashboard', () => {
  it('mantiene una tabla desktop y una lista móvil con los mismos datos clave', () => {
    const wrapper = mount(DashboardRecentPayments, {
      props: {
        pagos: [{
          id: 3,
          numero_recibo: 'REC-00000003',
          fecha: '2026-08-17',
          alumno_nombre: 'ACOSTA, Sasha De Los Angeles.',
          medio: 'efectivo',
          importe: 25000,
        }],
      },
    })

    expect(wrapper.get('.payments-table').text()).toContain('REC-00000003')
    const mobileCard = wrapper.get('.dashboard-payment-mobile-card')
    expect(mobileCard.text()).toContain('REC-00000003')
    expect(mobileCard.text()).toContain('ACOSTA, Sasha De Los Angeles.')
    expect(mobileCard.text()).toContain('$ 25.000,00')
    expect(mobileCard.text()).toContain('efectivo')
  })

  it('abre el pago seleccionado y permite consultar su recibo con el flujo compartido', async () => {
    getRecibo.mockResolvedValueOnce({ numero: 'REC-00000003', pago: { importe: '25000' }, aplicaciones: [] })
    const wrapper = mount(DashboardRecentPayments, {
      props: {
        pagos: [{
          id: 3,
          numero_recibo: 'REC-00000003',
          fecha: '2026-08-17',
          alumno_nombre: 'ACOSTA, Sasha De Los Angeles.',
          medio: 'efectivo',
          importe: 25000,
        }],
      },
      global: { stubs: { Teleport: true } },
    })

    await wrapper.find('.payments-table .dashboard-payment-detail-button').trigger('click')
    const detail = wrapper.getComponent({ name: 'OperacionDetalle' })
    expect(detail.props('operacion').id).toBe(3)
    expect(detail.props('tipo')).toBe('pago')

    await wrapper.findAll('button').find((button) => button.text() === 'Ver recibo').trigger('click')
    await wrapper.vm.$nextTick()
    expect(getRecibo).toHaveBeenCalledWith(3)
    expect(wrapper.text()).toContain('REC-00000003')

    await wrapper.findAll('button').find((button) => button.text() === 'Volver al detalle').trigger('click')
    await wrapper.findAll('button').find((button) => button.text() === 'Cerrar detalle').trigger('click')
    await wrapper.vm.$nextTick()
    await wrapper.find('.dashboard-payment-mobile-card .dashboard-payment-detail-button').trigger('click')
    expect(detail.props('operacion').id).toBe(3)

    wrapper.unmount()
  })
})
