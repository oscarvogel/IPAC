// Formateadores compartidos para la UI.
// Convencion: siempre devolver string, nunca null/undefined.

export function formatMoney(value, { fractionDigits = 0 } = {}) {
  const number = Number(value || 0)
  return number.toLocaleString('es-AR', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })
}

export function formatDate(value) {
  if (!value) return ''
  const isShort = typeof value === 'string' && value.length === 10
  const date = isShort ? new Date(`${value}T00:00:00`) : new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

export function formatDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
