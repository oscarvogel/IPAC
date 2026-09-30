import { toLocalISODate } from '@/lib/formatters'

export function periodoFechas(periodo, now = new Date()) {
  const hasta = toLocalISODate(now)
  if (periodo === 'hoy') return { desde: hasta, hasta }
  if (periodo === 'mes') return { desde: toLocalISODate(new Date(now.getFullYear(), now.getMonth(), 1)), hasta }
  return { desde: '', hasta: '' }
}

export function favoritaReporte(seccion, filtros, periodo) {
  const supportsPeriod = ['resumen', 'cobranzas', 'caja'].includes(seccion)
  const savedPeriod = supportsPeriod ? periodo : 'todos'
  return { seccion, periodo: savedPeriod, desde: savedPeriod === 'personalizado' ? filtros.desde : '', hasta: savedPeriod === 'personalizado' ? filtros.hasta : '', sucursal: filtros.sucursal ? Number(filtros.sucursal) : null, medio: ['resumen', 'cobranzas'].includes(seccion) ? filtros.medio || '' : '', usuario: ['caja', 'cobranzas'].includes(seccion) && filtros.usuario ? Number(filtros.usuario) : null }
}

export function filtrosFavorita(config) {
  return { ...(config.periodo === 'personalizado' ? { desde: config.desde, hasta: config.hasta } : periodoFechas(config.periodo)), sucursal: config.sucursal || '', medio: config.medio || '', usuario: config.usuario || '' }
}
