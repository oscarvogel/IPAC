import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAuth } from '@/composables/useAuth'
import * as api from '@/lib/api'

// Mockeamos el modulo de API para que useAuth no haga requests reales.
vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual('@/lib/api')
  return {
    ...actual,
    apiRequest: vi.fn(),
    setToken: vi.fn(),
    getToken: vi.fn(),
  }
})

const sampleMe = {
  id: 1,
  username: 'admin',
  perfil: { rol: 'administracion', sucursal: { id: 1, nombre: 'Posadas' } },
}

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    // useAuth tiene estado singleton a nivel de modulo, asi que reseteamos
    // el user entre tests para que no se filtre del test anterior.
    useAuth().logout()
  })

  it('login() exitoso guarda el token y setea el usuario', async () => {
    api.apiRequest
      .mockResolvedValueOnce({ key: 'tok-123' })
      .mockResolvedValueOnce(sampleMe)
    api.getToken.mockReturnValue('')

    const auth = useAuth()
    const ok = await auth.login('admin', 'admin123')

    expect(ok).toBe(true)
    expect(api.apiRequest).toHaveBeenCalledWith('/auth/login/', {
      method: 'POST',
      body: { username: 'admin', password: 'admin123' },
    })
    expect(api.setToken).toHaveBeenCalledWith('tok-123')
    expect(auth.user.value).toEqual(sampleMe)
    expect(auth.error.value).toBe('')
  })

  it('login() fallido devuelve false y setea el mensaje de error', async () => {
    api.apiRequest.mockRejectedValueOnce(new Error('Usuario o clave invalidos.'))

    const auth = useAuth()
    const ok = await auth.login('admin', 'wrong')

    expect(ok).toBe(false)
    expect(auth.user.value).toBeNull()
    expect(auth.error.value).toBe('Usuario o clave invalidos.')
  })

  it('logout() limpia token y usuario', () => {
    api.getToken.mockReturnValue('tok-123')
    const auth = useAuth()
    auth.logout()

    expect(api.setToken).toHaveBeenCalledWith(null)
    expect(auth.user.value).toBeNull()
    expect(auth.error.value).toBe('')
  })

  it('fetchCurrentUser() devuelve null si no hay token', async () => {
    api.getToken.mockReturnValue('')
    const auth = useAuth()
    const result = await auth.fetchCurrentUser()

    expect(result).toBeNull()
    expect(auth.user.value).toBeNull()
    expect(api.apiRequest).not.toHaveBeenCalled()
  })

  it('fetchCurrentUser() exitoso carga el usuario', async () => {
    api.getToken.mockReturnValue('tok-123')
    api.apiRequest.mockResolvedValueOnce(sampleMe)

    const auth = useAuth()
    const result = await auth.fetchCurrentUser()

    expect(result).toEqual(sampleMe)
    expect(auth.user.value).toEqual(sampleMe)
  })

  it('fetchCurrentUser() limpia el token si /auth/me/ falla', async () => {
    api.getToken.mockReturnValue('tok-123')
    api.apiRequest.mockRejectedValueOnce(new Error('Unauthorized'))

    const auth = useAuth()
    const result = await auth.fetchCurrentUser()

    expect(result).toBeNull()
    expect(auth.user.value).toBeNull()
    expect(api.setToken).toHaveBeenCalledWith(null)
  })
})
