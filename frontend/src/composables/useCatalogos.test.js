import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/lib/api', () => ({
  apiRequest: vi.fn(),
}))

const catalogResponses = () => ({ results: [] })

describe('carga compartida de catálogos', () => {
  let apiRequest
  let useCatalogos

  beforeEach(async () => {
    vi.resetModules()
    apiRequest = (await import('@/lib/api')).apiRequest
    const catalogsModule = await import('./useCatalogos')
    useCatalogos = catalogsModule.useCatalogos
    apiRequest.mockReset()
    apiRequest.mockResolvedValue(catalogResponses())
  })

  it('comparte la promesa y evita requests duplicados durante una carga en vuelo', async () => {
    const resolvers = []
    apiRequest.mockImplementation(() => new Promise((resolve) => {
      resolvers.push(resolve)
    }))

    const { loadCatalogos, loading } = useCatalogos()
    const firstLoad = loadCatalogos()
    const secondLoad = loadCatalogos()

    expect(secondLoad).toBe(firstLoad)
    expect(apiRequest).toHaveBeenCalledTimes(5)
    expect(loading.value).toBe(true)

    resolvers.forEach((resolve) => resolve(catalogResponses()))
    await firstLoad

    expect(loading.value).toBe(false)
  })

  it('libera la promesa cuando falla para permitir un reintento', async () => {
    apiRequest.mockRejectedValueOnce(new Error('offline'))

    const { loadCatalogos } = useCatalogos()
    await expect(loadCatalogos()).rejects.toThrow('offline')

    apiRequest.mockResolvedValue(catalogResponses())
    await loadCatalogos()

    expect(apiRequest).toHaveBeenCalledTimes(6)
  })

  it('permite cargar un catálogo crítico sin solicitar el paquete completo', async () => {
    const { loadCatalogo, sucursales, loaded } = useCatalogos()

    await loadCatalogo('sucursales')

    expect(apiRequest).toHaveBeenCalledTimes(1)
    expect(apiRequest).toHaveBeenCalledWith('/sucursales/')
    expect(sucursales.value).toEqual([])
    expect(loaded.value).toBe(false)
  })
})
