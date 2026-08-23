import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '@/lib/api'
import { useDeudores } from './useDeudores'

vi.mock('@/lib/api', () => ({
  apiRequest: vi.fn(),
}))

describe('useDeudores', () => {
  beforeEach(() => vi.clearAllMocks())

  it('consulta deuda y filtros en el backend y conserva la paginación', async () => {
    apiRequest.mockResolvedValue({
      count: 31,
      page: 2,
      page_size: 25,
      next: 'http://localhost:8000/api/deudores/?page=3',
      previous: 'http://localhost:8000/api/deudores/?page=1',
      results: [{ id: 7, deuda_total: '45000.00' }],
    })
    const { loadDeudores, deudores, pagination } = useDeudores()

    await loadDeudores({
      page: 2,
      page_size: 25,
      search: 'P-001',
      sucursal: 1,
      carrera: 4,
      vencidas: 1,
      deuda_min: 10000,
      orden: 'antiguedad',
    })

    expect(apiRequest).toHaveBeenCalledWith('/deudores/', {
      query: {
        page: 2,
        page_size: 25,
        search: 'P-001',
        sucursal: 1,
        carrera: 4,
        vencidas: 1,
        deuda_min: 10000,
        orden: 'antiguedad',
      },
    })
    expect(deudores.value).toEqual([{ id: 7, deuda_total: '45000.00' }])
    expect(pagination.value.count).toBe(31)
    expect(pagination.value.pageSize).toBe(25)
  })
})
