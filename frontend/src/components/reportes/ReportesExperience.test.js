import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ReporteFiltros from './ReporteFiltros.vue'
import ReporteResumen from './ReporteResumen.vue'
import PagosListado from './PagosListado.vue'

describe('experiencia de reportes', () => {
  it('sincroniza los filtros antes de solicitar el reporte', async () => {
    const wrapper = mount(ReporteFiltros, {
      props: {
        filtros: { desde: '', hasta: '', sucursal: '', medio: '' },
        sucursales: [{ id: 1, nombre: 'Posadas' }],
      },
    })

    const dates = wrapper.findAll('input[type="date"]')
    await dates[0].setValue('2026-07-01')
    await dates[1].setValue('2026-07-31')
    await wrapper.findAll('select')[0].setValue('1')
    await wrapper.findAll('select')[1].setValue('efectivo')
    await wrapper.get('.reports-apply-action').trigger('click')

    expect(wrapper.emitted('update:filtros')[0][0]).toEqual({
      desde: '2026-07-01',
      hasta: '2026-07-31',
      sucursal: 1,
      medio: 'efectivo',
    })
    expect(wrapper.emitted('aplicar')).toHaveLength(1)
  })

  it('presenta la distribución por medio ordenada por importe', () => {
    const wrapper = mount(ReporteResumen, {
      props: {
        resumen: {
          cobranzas: {
            total: 100000,
            cantidad_pagos: 3,
            por_medio: { efectivo: 25000, transferencia: 75000 },
          },
          cuenta_corriente: { deuda: 32000, saldo_a_favor: 20000, saldo_neto: 12000 },
          cajas: { cerradas: 2 },
        },
      },
    })

    const rows = wrapper.findAll('.reports-distribution-row')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('Transferencia')
    expect(rows[0].text()).toContain('75%')
    expect(wrapper.text()).toContain('3 pagos en el período')
    expect(wrapper.text()).toContain('Deuda pendiente')
    expect(wrapper.text()).toContain('$ 32.000,00')
    expect(wrapper.text()).toContain('Saldo a favor')
    expect(wrapper.text()).toContain('$ 20.000,00')
    expect(wrapper.text()).not.toContain('Deuda neta')
  })

  it('presenta cada pago como tarjeta móvil sin perder datos clave', () => {
    const wrapper = mount(PagosListado, {
      props: {
        pagos: [{
          id: 7,
          numero_recibo: 'REC-000007',
          fecha: '2026-07-31',
          alumno_nombre: 'Ana Gómez',
          concepto_nombre: 'Cuota mensual',
          sucursal_nombre: 'Posadas',
          medio: 'transferencia',
          importe: 25000,
        }],
      },
    })

    const card = wrapper.get('.reports-mobile-list .mobile-record-card')
    expect(card.text()).toContain('REC-000007')
    expect(card.text()).toContain('Ana Gómez')
    expect(card.text()).toContain('Cuota mensual')
    expect(card.get('.mobile-record-action').text()).toContain('Imprimir recibo')
  })
})
