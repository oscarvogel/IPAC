import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '@/lib/api'
import { useCarreras } from './useCarreras'

vi.mock('@/lib/api', () => ({
  apiRequest: vi.fn(),
}))

const carrera = {
  id: 1,
  nombre: 'Tecnicatura en Sistemas',
  tipo: 'carrera',
  sucursal: 1,
  cuota_programatica: '62000.00',
  cuota_extraprogramatica: '20000.00',
  cuota_total: '82000.00',
  activa: true,
}

describe('useCarreras', () => {
  beforeEach(() => vi.clearAllMocks())

  it('carga la lista y deja el error a la vista cuando la API falla', async () => {
    apiRequest.mockResolvedValueOnce({ results: [carrera] })

    const { carreras, error, loadCarreras } = useCarreras()
    await loadCarreras()

    expect(carreras.value).toEqual([carrera])
    expect(error.value).toBe('')
    expect(apiRequest).toHaveBeenCalledWith('/carreras/', { query: {} })
  })

  it('conserva el desglose programático al crear', async () => {
    apiRequest.mockResolvedValueOnce(carrera)

    const { createCarrera } = useCarreras()
    const guardado = await createCarrera({
      nombre: 'Tecnicatura en Sistemas',
      tipo: 'carrera',
      sucursal: 1,
      cuota_programatica: 62000,
      cuota_extraprogramatica: 20000,
      cuota_total: 82000,
    })

    expect(apiRequest).toHaveBeenCalledWith('/carreras/', {
      method: 'POST',
      body: expect.objectContaining({ cuota_programatica: 62000, cuota_extraprogramatica: 20000 }),
    })
    expect(guardado.cuota_programatica).toBe('62000.00')
  })

  it('desactiva con un PATCH y no borra la carrera', async () => {
    apiRequest.mockResolvedValueOnce({ results: [carrera] })
    const { loadCarreras, deactivateCarrera, carreras } = useCarreras()
    await loadCarreras()

    apiRequest.mockResolvedValueOnce({ ...carrera, activa: false })
    await deactivateCarrera(1)

    // La carrera tiene PROTECT contra Alumno, Matricula y ConceptoCobrable:
    // un DELETE rompería el historial de quien la haya cursado.
    expect(apiRequest).toHaveBeenCalledWith('/carreras/1/', {
      method: 'PATCH',
      body: { activa: false },
    })
    expect(carreras.value[0].activa).toBe(false)
  })

  it('expone el error del backend sin perder la lista anterior', async () => {
    apiRequest.mockResolvedValueOnce({ results: [carrera] })
    const { loadCarreras, error, carreras } = useCarreras()
    await loadCarreras()

    apiRequest.mockRejectedValueOnce(new Error('Sin permisos'))
    await loadCarreras()

    expect(error.value).toBe('Sin permisos')
    expect(carreras.value).toEqual([carrera])
  })
})