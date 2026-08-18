import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '@/lib/api'
import { useMatriculas } from './useMatriculas'

vi.mock('@/lib/api', () => ({
  apiRequest: vi.fn(),
}))

describe('useMatriculas', () => {
  beforeEach(() => vi.clearAllMocks())

  it('carga el historial por alumno y finaliza usando la acción del backend', async () => {
    apiRequest
      .mockResolvedValueOnce({ results: [{ id: 4, estado: 'activa' }] })
      .mockResolvedValueOnce({ id: 4, estado: 'finalizada', fecha_fin: '2026-08-17' })

    const { loadMatriculas, finalizarMatricula, matriculas } = useMatriculas()

    await loadMatriculas(12)
    await finalizarMatricula(4)

    expect(apiRequest).toHaveBeenNthCalledWith(1, '/matriculas/', { query: { alumno: 12 } })
    expect(apiRequest).toHaveBeenNthCalledWith(2, '/matriculas/4/finalizar/', { method: 'POST', body: {} })
    expect(matriculas.value).toEqual([{ id: 4, estado: 'finalizada', fecha_fin: '2026-08-17' }])
  })
})
