import { mount, flushPromises } from '@vue/test-utils'
import { ref, defineComponent } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import { useConsultasFavoritas } from './useConsultasFavoritas'
const state = vi.hoisted(() => ({ user: null, api: vi.fn() }))
vi.mock('@/lib/api', () => ({ apiRequest: (...args) => state.api(...args) }))
vi.mock('@/composables/useAuth', () => ({ useAuth: () => ({ user: state.user }) }))
describe('favoritas por cuenta y pantalla', () => {
  it('vacía al salir y descarta respuestas de la cuenta anterior', async () => {
    state.user = ref({ id: 1 })
    let resolveOld
    state.api.mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve })).mockResolvedValueOnce([{ id: 2, nombre: 'Cuenta dos' }])
    let prefs
    const wrapper = mount(defineComponent({ setup() { prefs = useConsultasFavoritas('reportes'); return () => null } }))
    state.user.value = { id: 2 }
    await flushPromises()
    expect(prefs.favoritas.value[0].id).toBe(2)
    resolveOld([{ id: 1, nombre: 'Cuenta uno' }]); await flushPromises()
    expect(prefs.favoritas.value[0].id).toBe(2)
    state.user.value = null
    expect(prefs.favoritas.value).toEqual([])
    expect(state.api).toHaveBeenCalledWith('/consultas-favoritas/', { query: { pantalla: 'reportes' } })
    wrapper.unmount()
  })
  it('la lectura para aplicar valida alcance y propaga errores sin aplicar', async () => {
    state.user = ref({ id: 1 }); state.api.mockResolvedValueOnce([])
    let prefs
    const wrapper = mount(defineComponent({ setup() { prefs = useConsultasFavoritas('caja'); return () => null } }))
    await flushPromises()
    state.api.mockRejectedValueOnce(new Error('Sucursal fuera de alcance'))
    await expect(prefs.obtener(7)).rejects.toThrow('Sucursal fuera de alcance')
    wrapper.unmount()
  })
})
