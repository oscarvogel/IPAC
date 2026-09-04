import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import ChangePasswordView from './ChangePasswordView.vue'

const mocks = vi.hoisted(() => ({
  changePassword: vi.fn().mockResolvedValue(true),
  error: { value: '' },
  loading: { value: false },
  push: vi.fn(),
}))

vi.mock('@/composables/useAuth', () => ({
  useAuth: () => mocks,
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mocks.push }),
}))

describe('ChangePasswordView', () => {
  it('rechaza claves diferentes sin llamar a la API', async () => {
    const wrapper = mount(ChangePasswordView)

    await wrapper.get('input[name="new_password"]').setValue('Nueva-Clave-IPAC-2026!')
    await wrapper.get('input[name="new_password_confirmation"]').setValue('Otra-Clave')
    await wrapper.get('form').trigger('submit')

    expect(mocks.changePassword).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('no coinciden')
  })

  it('cambia la clave y vuelve al dashboard', async () => {
    const wrapper = mount(ChangePasswordView)

    await wrapper.get('input[name="new_password"]').setValue('Nueva-Clave-IPAC-2026!')
    await wrapper.get('input[name="new_password_confirmation"]').setValue('Nueva-Clave-IPAC-2026!')
    await wrapper.get('form').trigger('submit')

    expect(mocks.changePassword).toHaveBeenCalledWith(
      'Nueva-Clave-IPAC-2026!',
      'Nueva-Clave-IPAC-2026!',
    )
    expect(mocks.push).toHaveBeenCalledWith('/dashboard')
  })
})
