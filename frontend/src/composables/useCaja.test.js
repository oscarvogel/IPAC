import { describe, it, expect } from 'vitest'
import { mapearResumenCaja } from '@/composables/useCaja'

describe('mapearResumenCaja', () => {
  it('devuelve importes en cero sin caja', () => {
    expect(mapearResumenCaja().totalCobrado).toBe(0)
    expect(mapearResumenCaja().efectivoEsperado).toBe(0)
  })

  it('consume el resumen calculado por backend sin reconstruir reglas contables', () => {
    const out = mapearResumenCaja({
      total_esperado: '160000.00',
      saldo_final_fisico: '160000.00',
      resumen: {
        saldo_inicial: '20000.00',
        cobranzas_efectivo: '150000.00',
        otros_ingresos_efectivo: '0.00',
        egresos_efectivo: '10000.00',
        retiros_efectivo: '0.00',
        efectivo_esperado: '160000.00',
        total_ingresos: '270000.00',
        total_egresos: '10000.00',
        total_cobrado: '270000.00',
        efectivo: '150000.00',
        transferencia: '80000.00',
        mercado_pago: '40000.00',
        tarjeta: '0.00',
        otro: '0.00',
      },
    })

    expect(out.saldoInicial).toBe(20000)
    expect(out.efectivoEsperado).toBe(160000)
    expect(out.totalCobrado).toBe(270000)
    expect(out.transferencia).toBe(80000)
    expect(out.mercadoPago).toBe(40000)
  })
})
