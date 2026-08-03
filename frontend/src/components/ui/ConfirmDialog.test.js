import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ConfirmDialog from './ConfirmDialog.vue'

function mountDialog(props = {}) {
  return mount(ConfirmDialog, {
    props: {
      open: true,
      title: 'Desactivar alumno',
      description: 'Esta acción impedirá que el alumno siga operando.',
      subject: 'Ana Gómez',
      confirmLabel: 'Desactivar',
      ...props,
    },
    global: {
      stubs: { Teleport: true },
    },
  })
}

describe('ConfirmDialog', () => {
  it('expone el contexto de la acción y emite la decisión elegida', async () => {
    const wrapper = mountDialog()

    expect(wrapper.get('[role="alertdialog"]').attributes('aria-modal')).toBe('true')
    expect(wrapper.text()).toContain('Desactivar alumno')
    expect(wrapper.text()).toContain('Ana Gómez')

    await wrapper.get('.confirm-cancel').trigger('click')
    expect(wrapper.emitted('cancel')).toHaveLength(1)

    await wrapper.get('.confirm-submit').trigger('click')
    expect(wrapper.emitted('confirm')).toHaveLength(1)
  })

  it('bloquea ambas acciones mientras se procesa la solicitud', () => {
    const wrapper = mountDialog({ loading: true })

    expect(wrapper.get('.confirm-cancel').attributes('disabled')).toBeDefined()
    expect(wrapper.get('.confirm-submit').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Procesando')
  })
})
