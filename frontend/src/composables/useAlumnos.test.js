import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '@/lib/api'
import { useAlumnos } from './useAlumnos'

vi.mock('@/lib/api', () => ({
  apiRequest: vi.fn(),
}))

describe('useAlumnos', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('envía búsqueda y filtros al backend y conserva metadatos de paginación', async () => {
    apiRequest.mockResolvedValue({
      count: 123,
      page: 2,
      page_size: 25,
      next: 'http://localhost:8000/api/alumnos/?page=3',
      previous: 'http://localhost:8000/api/alumnos/?page=1',
      results: [{ id: 101, nombre: 'Lucia' }],
    })
    const { loadAlumnos, pagination, alumnos } = useAlumnos()

    await loadAlumnos({ page: 2, page_size: 25, search: 'Lucia', sucursal: 1, estado: 'activo' })

    expect(apiRequest).toHaveBeenCalledWith('/alumnos/', {
      query: { page: 2, page_size: 25, search: 'Lucia', sucursal: 1, estado: 'activo' },
    })
    expect(pagination.value).toEqual({
      count: 123,
      page: 2,
      pageSize: 25,
      next: 'http://localhost:8000/api/alumnos/?page=3',
      previous: 'http://localhost:8000/api/alumnos/?page=1',
    })
    expect(alumnos.value).toEqual([{ id: 101, nombre: 'Lucia' }])
  })

  it('carga métricas globales independientes de la página actual', async () => {
    apiRequest.mockResolvedValue({ total: 300, activos: 287, inactivos: 13 })
    const { loadAlumnoStats, alumnoStats } = useAlumnos()

    await loadAlumnoStats({ sucursal: 1, estado: '' })

    expect(apiRequest).toHaveBeenCalledWith('/alumnos/estadisticas/', {
      query: { sucursal: 1, estado: '' },
    })
    expect(alumnoStats.value).toEqual({ total: 300, activos: 287, inactivos: 13 })
  })
})
