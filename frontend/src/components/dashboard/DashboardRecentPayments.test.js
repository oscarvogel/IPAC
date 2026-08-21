import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import DashboardRecentPayments from './DashboardRecentPayments.vue'

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
})
