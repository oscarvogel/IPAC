import { describe, it, expect } from 'vitest'
import { formatMoney, formatDate, formatDateTime } from '@/lib/formatters'

describe('formatters', () => {
  describe('formatMoney', () => {
    it('formatea numeros con separador de miles estilo es-AR', () => {
      expect(formatMoney(1234567.89, { fractionDigits: 2 })).toBe('1.234.567,89')
    })

    it('sin decimales por default', () => {
      expect(formatMoney(50000)).toBe('50.000')
    })

    it('acepta string y number', () => {
      expect(formatMoney('1234.5', { fractionDigits: 2 })).toBe('1.234,50')
    })

    it('tolera null/undefined y devuelve 0', () => {
      expect(formatMoney(null)).toBe('0')
      expect(formatMoney(undefined)).toBe('0')
    })
  })

  describe('formatDate', () => {
    it('formatea una fecha corta AAAA-MM-DD', () => {
      expect(formatDate('2026-07-25')).toBe('25/07/2026')
    })

    it('devuelve vacio para null/undefined', () => {
      expect(formatDate(null)).toBe('')
      expect(formatDate(undefined)).toBe('')
    })
  })

  describe('formatDateTime', () => {
    it('formatea fecha y hora ISO', () => {
      const out = formatDateTime('2026-07-25T14:30:00Z')
      // La salida exacta depende de la zona horaria del runner; verificamos
      // solo que arranque con dd/mm/aaaa, hh:mm.
      expect(out).toMatch(/^\d{2}\/\d{2}\/\d{4}, \d{2}:\d{2}/)
    })

    it('devuelve vacio para null/undefined', () => {
      expect(formatDateTime(null)).toBe('')
      expect(formatDateTime(undefined)).toBe('')
    })
  })
})
