import { afterEach, describe, expect, it, vi } from 'vitest'
import { printDocument } from './print'

describe('printDocument', () => {
  afterEach(() => {
    delete document.documentElement.dataset.printTarget
    vi.restoreAllMocks()
  })

  it('selecciona el recibo y limpia el destino al cerrar la vista previa', () => {
    vi.spyOn(window, 'print').mockImplementation(() => {})

    printDocument('receipt')

    expect(document.documentElement.dataset.printTarget).toBe('receipt')
    expect(window.print).toHaveBeenCalledTimes(1)
    window.dispatchEvent(new Event('afterprint'))
    expect(document.documentElement.dataset.printTarget).toBeUndefined()
  })

  it('selecciona el resumen de caja y rechaza destinos desconocidos', () => {
    vi.spyOn(window, 'print').mockImplementation(() => {})

    printDocument('cash-summary')
    expect(document.documentElement.dataset.printTarget).toBe('cash-summary')
    printDocument('unknown')

    expect(window.print).toHaveBeenCalledTimes(1)
    expect(document.documentElement.dataset.printTarget).toBe('cash-summary')
  })
})
