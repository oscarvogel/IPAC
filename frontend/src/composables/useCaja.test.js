import { describe, it, expect } from 'vitest'
import { calcularTotalesCaja } from '@/composables/useCaja'

describe('calcularTotalesCaja', () => {
  it('devuelve todos los medios en 0 cuando no hay movimientos', () => {
    expect(calcularTotalesCaja([])).toEqual({
      total: 0,
      efectivo: 0,
      transferencia: 0,
      tarjeta: 0,
      otro: 0,
    })
  })

  it('suma pagos en positivo', () => {
    const movimientos = [
      { tipo: 'pago', medio: 'efectivo', importe: '50000' },
      { tipo: 'pago', medio: 'transferencia', importe: '22000' },
    ]
    const out = calcularTotalesCaja(movimientos)
    expect(out.total).toBe(72000)
    expect(out.efectivo).toBe(50000)
    expect(out.transferencia).toBe(22000)
  })

  it('resta egresos, retiros y pases del total', () => {
    const movimientos = [
      { tipo: 'pago', medio: 'efectivo', importe: '100000' },
      { tipo: 'egreso', medio: 'efectivo', importe: '10000' },
      { tipo: 'retiro', medio: 'efectivo', importe: '5000' },
      { tipo: 'pase', medio: 'efectivo', importe: '2000' },
    ]
    const out = calcularTotalesCaja(movimientos)
    // 100k - 10k - 5k - 2k = 83k
    expect(out.total).toBe(83000)
    expect(out.efectivo).toBe(83000)
  })

  it('ingresos manuales suman al total y al medio correspondiente', () => {
    const movimientos = [
      { tipo: 'ingreso', medio: 'tarjeta', importe: '7500' },
      { tipo: 'ingreso', medio: 'otro', importe: '1500' },
    ]
    const out = calcularTotalesCaja(movimientos)
    expect(out.total).toBe(9000)
    expect(out.tarjeta).toBe(7500)
    expect(out.otro).toBe(1500)
  })

  it('tolera movimientos con importe como numero o string', () => {
    const movimientos = [
      { tipo: 'pago', medio: 'efectivo', importe: 1000 },
      { tipo: 'pago', medio: 'efectivo', importe: '500' },
    ]
    expect(calcularTotalesCaja(movimientos).total).toBe(1500)
  })

  it('mezcla todos los medios en una sola operacion', () => {
    const movimientos = [
      { tipo: 'pago', medio: 'efectivo', importe: '1000' },
      { tipo: 'pago', medio: 'transferencia', importe: '2000' },
      { tipo: 'pago', medio: 'tarjeta', importe: '3000' },
      { tipo: 'pago', medio: 'otro', importe: '500' },
      { tipo: 'egreso', medio: 'efectivo', importe: '200' },
    ]
    const out = calcularTotalesCaja(movimientos)
    expect(out.total).toBe(6300)
    expect(out.efectivo).toBe(800)
    expect(out.transferencia).toBe(2000)
    expect(out.tarjeta).toBe(3000)
    expect(out.otro).toBe(500)
  })
})
