import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import CajaHero from './CajaHero.vue'
import CajaMovimientos from './CajaMovimientos.vue'

describe('experiencia de caja', () => {
  it('mantiene disponibles las operaciones de una caja abierta', async () => {
    const wrapper = mount(CajaHero, {
      props: {
        cajaHoy: {
          fecha: '2026-07-31',
          estado: 'abierta',
          sucursal_nombre: 'Posadas',
        },
        puedeMover: true,
      },
    })

    expect(wrapper.text()).toContain('Posadas')
    expect(wrapper.find('.cash-status-badge').text()).toContain('abierta')

    const buttons = wrapper.findAll('button')
    await buttons.find((button) => button.text().includes('Ingreso')).trigger('click')
    await buttons.find((button) => button.text().includes('Cerrar caja')).trigger('click')

    expect(wrapper.emitted('movimiento')[0]).toEqual(['ingreso'])
    expect(wrapper.emitted('cerrar')).toHaveLength(1)
  })

  it('diferencia visualmente ingresos y egresos en el historial', () => {
    const wrapper = mount(CajaMovimientos, {
      props: {
        movimientos: [
          {
            id: 1,
            tipo: 'ingreso',
            tipo_label: 'Ingreso',
            medio: 'efectivo',
            descripcion: 'Apertura',
            importe: 15000,
          },
          {
            id: 2,
            tipo: 'egreso',
            tipo_label: 'Egreso',
            medio: 'efectivo',
            descripcion: 'Insumos',
            importe: 3000,
          },
        ],
      },
    })

    const amounts = wrapper.findAll('.cash-movement-amount')
    expect(amounts[0].text()).toContain('+')
    expect(amounts[0].classes()).not.toContain('negative')
    expect(amounts[1].text()).toContain('−')
    expect(amounts[1].classes()).toContain('negative')

    const mobileCards = wrapper.findAll('.cash-mobile-list .mobile-record-card')
    expect(mobileCards).toHaveLength(2)
    expect(mobileCards[0].text()).toContain('Apertura')
    expect(mobileCards[1].get('.mobile-record-amount').classes()).toContain('negative')
  })
})
