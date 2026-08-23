import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '@/lib/api'
import { useCuotasMasivas } from './useCuotasMasivas'

vi.mock('@/lib/api', () => ({
  apiRequest: vi.fn(),
}))

describe('useCuotasMasivas', () => {
  beforeEach(() => vi.clearAllMocks())

  it('calcula alumnos activos elegibles y omite duplicados del mismo concepto y periodo', async () => {
    apiRequest.mockResolvedValueOnce({
      alumnos_encontrados: 2,
      omitidas: 1,
      alumnos_elegibles: [2],
    })

    const { evaluar, alumnosElegibles, alumnosEncontrados, omitidas } = useCuotasMasivas()
    await evaluar({ sucursal: 3, carrera: '', concepto: 10, periodo: '2026-08' })

    expect(alumnosEncontrados.value).toBe(2)
    expect(omitidas.value).toBe(1)
    expect(alumnosElegibles.value.map((alumno) => alumno.id)).toEqual([2])
    expect(apiRequest).toHaveBeenCalledWith('/cuotas/evaluar-generacion/', {
      method: 'POST',
      body: { sucursal: 3, carrera: null, concepto: 10, periodo: '2026-08' },
    })
  })

  it('envia todos los ids elegibles al endpoint masivo', async () => {
    apiRequest.mockResolvedValue({ count: 0, results: [] })
    const { generar } = useCuotasMasivas()
    const payload = { alumnos: [4, 8, 15], concepto: 10, periodo: '2026-09' }

    await generar(payload)

    expect(apiRequest).toHaveBeenCalledWith('/cuotas/generar/', { method: 'POST', body: payload })
  })
})
