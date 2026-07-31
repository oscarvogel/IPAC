import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ReporteFiltros from './ReporteFiltros.vue'
import ReporteResumen from './ReporteResumen.vue'

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
          cuenta_corriente: { saldo_neto: 12000 },
          cajas: { cerradas: 2 },
        },
      },
    })

    const rows = wrapper.findAll('.reports-distribution-row')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('Transferencia')
    expect(rows[0].text()).toContain('75%')
    expect(wrapper.text()).toContain('3 pagos en el período')
  })
})
