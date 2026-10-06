import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '@/lib/api'
import { useCuotasMasivas } from './useCuotasMasivas'

vi.mock('@/lib/api', () => ({
  apiRequest: vi.fn(),
}))

const LOTE = { cantidad: 4, mes_inicial: 3, anio_inicial: 2026, dia_vencimiento: 10 }
const MES = { periodo: '2026-08', fecha_vencimiento: '2026-08-10' }

describe('useCuotasMasivas', () => {
  beforeEach(() => vi.clearAllMocks())

  it('calcula alumnos elegibles y quien ya completo el lote', async () => {
    apiRequest.mockResolvedValueOnce({
      cantidad_periodos: 4,
      periodos: ['2026-03', '2026-04', '2026-05', '2026-06'],
      etiquetas_periodo: ['marzo 2026 (vence el 10)'],
      alumnos_encontrados: 2,
      omitidas: 1,
      alumnos_elegibles: [2],
      cuotas_a_generar: 3,
      detalle_alumnos: [
        { id: 1, legajo: 'P-001', nombre_completo: 'Perez, Pedro', motivo: 'Ya tiene todas las cuotas del lote.', faltantes: [], existentes: ['2026-03'] },
        { id: 2, legajo: 'P-002', nombre_completo: 'Lopez, Ana', motivo: '', faltantes: ['2026-03', '2026-04'], existentes: [] },
      ],
    })

    const { evaluar, alumnosElegibles, alumnosEncontrados, omitidas, detalleAlumnos, periodos, cuotasAGenerar } = useCuotasMasivas()
    await evaluar({ sucursal: 3, carrera: '', concepto: 10, plan: LOTE })

    expect(alumnosEncontrados.value).toBe(2)
    expect(omitidas.value).toBe(1)
    expect(alumnosElegibles.value.map((alumno) => alumno.id)).toEqual([2])
    expect(alumnosElegibles.value[0].faltantes).toEqual(['2026-03', '2026-04'])
    expect(periodos.value).toHaveLength(4)
    expect(cuotasAGenerar.value).toBe(3)
    expect(detalleAlumnos.value).toHaveLength(2)
  })

  it('envia el plan del lote al backend sin transformarlo', async () => {
    apiRequest.mockResolvedValueOnce({ alumnos_encontrados: 0, alumnos_elegibles: [] })
    const { evaluar } = useCuotasMasivas()

    await evaluar({ sucursal: 3, carrera: '', concepto: 10, plan: LOTE })

    expect(apiRequest).toHaveBeenCalledWith('/cuotas/evaluar-generacion/', {
      method: 'POST',
      body: { sucursal: 3, carrera: null, concepto: 10, ...LOTE },
    })
  })

  it('manda el alumno cuando la reinscripcion acota la previsualizacion a uno', async () => {
    apiRequest.mockResolvedValueOnce({ alumnos_encontrados: 1, alumnos_elegibles: [284], cuotas_a_generar: 10 })

    const { evaluar } = useCuotasMasivas()
    await evaluar({ sucursal: 1, carrera: 4, concepto: 7, alumno: 284, plan: LOTE })

    expect(apiRequest).toHaveBeenCalledWith('/cuotas/evaluar-generacion/', {
      method: 'POST',
      body: { sucursal: 1, carrera: 4, concepto: 7, alumno: 284, ...LOTE },
    })
  })

  it('omite el filtro cuando no viene alumno, para no romper la masiva', async () => {
    apiRequest.mockResolvedValueOnce({ alumnos_encontrados: 3, alumnos_elegibles: [1, 2, 3] })

    const { evaluar } = useCuotasMasivas()
    await evaluar({ sucursal: 1, carrera: 4, concepto: 7, plan: LOTE })

    const body = apiRequest.mock.calls[0][1].body
    expect(body).not.toHaveProperty('alumno')
    expect(body.carrera).toBe(4)
  })

  it('sigue soportando el camino de un solo periodo', async () => {
    apiRequest.mockResolvedValueOnce({
      periodos: ['2026-08'],
      etiquetas_periodo: ['agosto 2026 (vence el 10)'],
      alumnos_encontrados: 1,
      omitidas: 0,
      alumnos_elegibles: [1],
      cuotas_a_generar: 1,
      detalle_alumnos: [{ id: 1, nombre_completo: 'Perez, Pedro', motivo: '', faltantes: ['2026-08'], existentes: [] }],
    })

    const { evaluar, periodos, cuotasAGenerar } = useCuotasMasivas()
    await evaluar({ sucursal: 3, concepto: 10, plan: MES })

    expect(periodos.value).toEqual(['2026-08'])
    expect(cuotasAGenerar.value).toBe(1)
    expect(apiRequest).toHaveBeenCalledWith('/cuotas/evaluar-generacion/', {
      method: 'POST',
      body: { sucursal: 3, carrera: null, concepto: 10, ...MES },
    })
  })

  it('no llama al backend si falta el plan', async () => {
    const { evaluar, alumnosEncontrados } = useCuotasMasivas()

    await evaluar({ sucursal: 3, concepto: 10, plan: null })

    expect(apiRequest).not.toHaveBeenCalled()
    expect(alumnosEncontrados.value).toBe(0)
  })

  it('limpia el estado del lote anterior cuando el plan pasa a ser invalido', async () => {
    const { evaluar, periodos, cuotasAGenerar } = useCuotasMasivas()
    apiRequest.mockResolvedValueOnce({
      periodos: ['2026-03', '2026-04'],
      alumnos_encontrados: 1,
      alumnos_elegibles: [1],
      cuotas_a_generar: 2,
      detalle_alumnos: [{ id: 1, motivo: '', faltantes: ['2026-03', '2026-04'] }],
    })
    await evaluar({ sucursal: 3, concepto: 10, plan: LOTE })
    expect(periodos.value).toHaveLength(2)

    await evaluar({ sucursal: 3, concepto: 10, plan: null })

    expect(periodos.value).toEqual([])
    expect(cuotasAGenerar.value).toBe(0)
  })

  it('mantiene compatible una respuesta previa que no incluya detalle', async () => {
    apiRequest.mockResolvedValueOnce({ alumnos_encontrados: 1, omitidas: 0, alumnos_elegibles: [9] })
    const { evaluar, alumnosElegibles, detalleAlumnos } = useCuotasMasivas()

    await evaluar({ sucursal: 3, concepto: 10, plan: MES })

    expect(alumnosElegibles.value).toEqual([{ id: 9 }])
    expect(detalleAlumnos.value).toEqual([])
  })

  it('envia todos los ids elegibles al endpoint masivo', async () => {
    apiRequest.mockResolvedValue({ cuotas: [], resumen: { creadas: 0, omitidas: 0 } })
    const { generar } = useCuotasMasivas()
    const payload = { alumnos: [4, 8, 15], concepto: 10, ...LOTE }

    await generar(payload)

    expect(apiRequest).toHaveBeenCalledWith('/cuotas/generar/', { method: 'POST', body: payload })
  })
})
