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
      detalle_alumnos: [
        { id: 1, legajo: 'P-001', nombre_completo: 'Perez, Pedro', motivo: 'Ya existe una cuota.' },
        { id: 2, legajo: 'P-002', nombre_completo: 'Lopez, Ana', motivo: '' },
      ],
    })

    const { evaluar, alumnosElegibles, alumnosEncontrados, omitidas, detalleAlumnos } = useCuotasMasivas()
    await evaluar({ sucursal: 3, carrera: '', concepto: 10, periodo: '2026-08' })

    expect(alumnosEncontrados.value).toBe(2)
    expect(omitidas.value).toBe(1)
    expect(alumnosElegibles.value.map((alumno) => alumno.id)).toEqual([2])
    expect(alumnosElegibles.value[0].nombre_completo).toBe('Lopez, Ana')
    expect(detalleAlumnos.value).toHaveLength(2)
    expect(apiRequest).toHaveBeenCalledWith('/cuotas/evaluar-generacion/', {
      method: 'POST',
      body: { sucursal: 3, carrera: null, concepto: 10, periodo: '2026-08' },
    })
  })

  it('mantiene compatible una respuesta previa que no incluya detalle', async () => {
    apiRequest.mockResolvedValueOnce({ alumnos_encontrados: 1, omitidas: 0, alumnos_elegibles: [9] })
    const { evaluar, alumnosElegibles, detalleAlumnos } = useCuotasMasivas()

    await evaluar({ sucursal: 3, concepto: 10, periodo: '2026-08' })

    expect(alumnosElegibles.value).toEqual([{ id: 9 }])
    expect(detalleAlumnos.value).toEqual([])
  })

  it('envia todos los ids elegibles al endpoint masivo', async () => {
    apiRequest.mockResolvedValue({ count: 0, results: [] })
    const { generar } = useCuotasMasivas()
    const payload = { alumnos: [4, 8, 15], concepto: 10, periodo: '2026-09' }

    await generar(payload)

    expect(apiRequest).toHaveBeenCalledWith('/cuotas/generar/', { method: 'POST', body: payload })
  })
})
