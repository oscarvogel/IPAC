// Wrapper de fetch con manejo de token, errores normalizados y soporte para query string.
//
// Reglas:
// - Si la respuesta es 204, devuelve null.
// - Si la respuesta es 401, limpia el token para que el guard del router redirija al login.
// - Si la respuesta no es 2xx, lanza un ApiError con `message` legible para la UI.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const TOKEN_KEY = 'ipac_token'

export { API_BASE_URL }

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token, { persistent = true } = {}) {
  localStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(TOKEN_KEY)

  if (token) {
    const storage = persistent ? localStorage : sessionStorage
    storage.setItem(TOKEN_KEY, token)
  }
}

export class ApiError extends Error {
  constructor(message, { status = 0, payload = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

function buildUrl(path, query) {
  let url = `${API_BASE_URL}${path}`
  if (query && typeof query === 'object') {
    const params = new URLSearchParams()
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === '') continue
      params.set(key, String(value))
    }
    const qs = params.toString()
    if (qs) url += `?${qs}`
  }
  return url
}

function pickErrorMessage(payload) {
  if (!payload) return 'No se pudo completar la operacion.'
  if (typeof payload === 'string') return payload
  if (typeof payload.detail === 'string') return payload.detail
  if (Array.isArray(payload.non_field_errors) && payload.non_field_errors.length) {
    return payload.non_field_errors.join(' ')
  }
  if (typeof payload === 'object') {
    const firstKey = Object.keys(payload)[0]
    if (firstKey) {
      const value = payload[firstKey]
      if (Array.isArray(value)) return `${firstKey}: ${value.join(' ')}`
      if (typeof value === 'string') return `${firstKey}: ${value}`
    }
  }
  return 'No se pudo completar la operacion.'
}

export async function apiRequest(path, options = {}) {
  const { method = 'GET', body, query, headers = {}, raw = false } = options
  const url = buildUrl(path, query)

  const finalHeaders = {
    'Content-Type': 'application/json',
    ...headers,
  }
  const token = getToken()
  if (token) finalHeaders.Authorization = `Token ${token}`

  const fetchOptions = {
    method,
    headers: finalHeaders,
  }
  if (body !== undefined && body !== null) {
    fetchOptions.body = typeof body === 'string' ? body : JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(url, fetchOptions)
  } catch (networkError) {
    throw new ApiError('No se pudo conectar con el servidor.', { status: 0 })
  }

  if (response.status === 204) return null

  if (response.status === 401) {
    setToken(null)
  }

  let payload = null
  const text = await response.text()
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = text
    }
  }

  if (!response.ok) {
    throw new ApiError(pickErrorMessage(payload), { status: response.status, payload })
  }

  if (raw) return response
  return payload
}

export async function uploadFile(path, file, fields = {}) {
  const formData = new FormData()
  formData.append('archivo', file)
  for (const [key, value] of Object.entries(fields)) {
    if (value !== undefined && value !== null && value !== '') formData.append(key, String(value))
  }

  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Token ${token}`

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { method: 'POST', headers, body: formData })
  } catch {
    throw new ApiError('No se pudo conectar con el servidor.', { status: 0 })
  }

  if (response.status === 401) setToken(null)
  const text = await response.text()
  let payload = null
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = text
    }
  }
  if (!response.ok) throw new ApiError(pickErrorMessage(payload), { status: response.status, payload })
  return payload
}

export async function downloadFile(path) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Token ${token}`
  const response = await fetch(`${API_BASE_URL}${path}`, { headers })
  if (!response.ok) {
    const text = await response.text()
    let payload = null
    try {
      payload = text ? JSON.parse(text) : null
    } catch {
      payload = text
    }
    throw new ApiError(pickErrorMessage(payload), { status: response.status, payload })
  }
  return response.blob()
}
