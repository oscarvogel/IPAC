import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import DesktopLogin from './DesktopLogin.vue'
import MobileLogin from './MobileLogin.vue'

describe('experiencias de login independientes', () => {
  it('el desktop emite sus propias credenciales y preferencia de sesion', async () => {
    const wrapper = mount(DesktopLogin)

    await wrapper.get('input[name="username"]').setValue('admin')
    await wrapper.get('input[name="password"]').setValue('admin123')
    await wrapper.get('input[type="checkbox"]').setValue(true)
    await wrapper.get('form').trigger('submit')

    expect(wrapper.find('.desktop-login-form').exists()).toBe(true)
    expect(wrapper.emitted('submit')[0][0]).toEqual({
      username: 'admin',
      password: 'admin123',
      remember: true,
    })
  })

  it('el mobile mantiene un formulario y una estructura propios', async () => {
    const wrapper = mount(MobileLogin)

    await wrapper.get('input[name="username"]').setValue('caja')
    await wrapper.get('input[name="password"]').setValue('clave')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.find('.mobile-login-form').exists()).toBe(true)
    expect(wrapper.find('.desktop-login-form').exists()).toBe(false)
    expect(wrapper.emitted('submit')[0][0]).toEqual({
      username: 'caja',
      password: 'clave',
      remember: false,
    })
  })
})
