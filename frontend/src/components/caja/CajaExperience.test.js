import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import CajaHero from './CajaHero.vue'
import CajaMovimientos from './CajaMovimientos.vue'
import CerrarCajaModal from './CerrarCajaModal.vue'

const confirmCierreCaja = vi.hoisted(() => vi.fn().mockResolvedValue({ isConfirmed: false }))
vi.mock('@/lib/swal', () => ({ confirmCierreCaja }))

describe('experiencia de caja', () => {
  it('explica el cálculo de diferencia y la distribución del efectivo antes del cierre', async () => {
    const wrapper = mount(CerrarCajaModal, {
      props: {
        open: true,
        totalEsperado: 100,
        cajaHoy: { id: 1, fecha: '2026-09-26', estado: 'abierta', sucursal_nombre: 'Posadas' },
      },
      global: {
        stubs: {
          Teleport: true,
          AppModalTransition: { template: '<div><slot /></div>' },
          AppButtonContent: { template: '<span>{{ label }}</span>', props: ['label'] },
        },
      },
    })

    expect(wrapper.text()).toContain('total contado menos total esperado')
    expect(wrapper.text()).toContain('deben sumar el total contado')
    await wrapper.find('input[type="number"]').setValue('90')
    expect(wrapper.text()).toContain('Hay una diferencia entre el total esperado y el total contado.')
  })

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
    expect(wrapper.find('.cash-status-badge').text()).toContain('Abierta')

    const buttons = wrapper.findAll('button')
    expect(wrapper.text()).toContain('Ingreso manual')
    expect(wrapper.text()).toContain('Egreso manual')
    expect(wrapper.text()).toContain('Retiro de efectivo')
    await buttons.find((button) => button.text().includes('Ingreso manual')).trigger('click')
    await buttons.find((button) => button.text().includes('Cerrar caja')).trigger('click')

    expect(wrapper.emitted('movimiento')[0]).toEqual(['ingreso'])
    expect(wrapper.emitted('cerrar')).toHaveLength(1)
  })

  it('prioriza consulta e impresión cuando la caja está cerrada', () => {
    const wrapper = mount(CajaHero, {
      props: {
        cajaHoy: {
          fecha: '2026-07-31',
          estado: 'cerrada',
          sucursal_nombre: 'Posadas',
          usuario_nombre: 'cajero',
          cerrada_en: '2026-07-31T18:30:00-03:00',
        },
        puedeMover: false,
      },
    })

    expect(wrapper.text()).toContain('Caja cerrada')
    expect(wrapper.text()).toContain('Imprimir cierre')
    expect(wrapper.text()).not.toContain('Ingreso manual')
    expect(wrapper.text()).not.toContain('Cerrar caja')
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
