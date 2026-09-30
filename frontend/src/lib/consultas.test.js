import { describe, expect, it } from 'vitest'
import { periodoFechas, favoritaReporte, filtrosFavorita } from './consultas'
describe('períodos y configuración de consultas', () => {
  it('usa días locales y mes hasta hoy', () => {
    const now = new Date(2026, 8, 30, 23, 59)
    expect(periodoFechas('hoy', now)).toEqual({ desde: '2026-09-30', hasta: '2026-09-30' })
    expect(periodoFechas('mes', now)).toEqual({ desde: '2026-09-01', hasta: '2026-09-30' })
  })
  it('conserva fechas personalizadas y elimina filtros no aplicables', () => {
    const config = favoritaReporte('caja', { desde: '2026-08-01', hasta: '2026-08-20', medio: 'tarjeta', sucursal: '2', usuario: '3', busqueda: 'privada' }, 'personalizado')
    expect(config).toEqual({ seccion: 'caja', periodo: 'personalizado', desde: '2026-08-01', hasta: '2026-08-20', medio: '', sucursal: 2, usuario: 3 })
    expect(filtrosFavorita(config).desde).toBe('2026-08-01')
    expect(favoritaReporte('resumen', {}, 'mes')).toEqual(expect.objectContaining({ desde: '', hasta: '', usuario: null }))
  })
})
