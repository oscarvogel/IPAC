import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { vFocusTrap, vFormValidation } from './accessibility'

describe('directivas de accesibilidad', () => {
  beforeEach(() => {
    vi.stubGlobal('requestAnimationFrame', (callback) => {
      callback()
      return 1
    })
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('mantiene el foco dentro del diálogo, responde a Escape y restaura el foco previo', async () => {
    const trigger = document.createElement('button')
    trigger.textContent = 'Abrir'
    document.body.appendChild(trigger)
    trigger.focus()
    const close = vi.fn()

    const wrapper = mount({
      props: ['close'],
      template: `
        <section v-focus-trap="{ close }" tabindex="-1">
          <input id="first-control" />
          <button id="last-control" type="button">Terminar</button>
        </section>
      `,
    }, {
      props: { close },
      attachTo: document.body,
      global: { directives: { focusTrap: vFocusTrap } },
    })

    expect(document.activeElement.id).toBe('first-control')

    const last = wrapper.get('#last-control')
    last.element.focus()
    await last.trigger('keydown', { key: 'Tab' })
    expect(document.activeElement.id).toBe('first-control')

    await wrapper.get('section').trigger('keydown', { key: 'Escape' })
    expect(close).toHaveBeenCalledOnce()

    wrapper.unmount()
    expect(document.activeElement).toBe(trigger)
  })

  it('anuncia errores después de interactuar y los elimina al corregir el campo', async () => {
    const wrapper = mount({
      template: `
        <form v-form-validation>
          <label>Email <input name="email" type="email" required /></label>
        </form>
      `,
    }, {
      global: { directives: { formValidation: vFormValidation } },
    })

    const input = wrapper.get('input')
    await input.trigger('focusout')

    expect(input.attributes('aria-invalid')).toBe('true')
    expect(wrapper.get('[role="alert"]').text()).toContain('obligatorio')
    const feedbackId = wrapper.get('[role="alert"]').attributes('id')
    expect(input.attributes('aria-describedby')).toBe(feedbackId)

    await input.setValue('persona@ipac.edu.ar')
    expect(input.attributes('aria-invalid')).toBeUndefined()
    expect(document.getElementById(feedbackId)).toBeNull()
  })
})
