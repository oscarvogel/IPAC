import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import AppTooltipLayer from './AppTooltipLayer.vue'

describe('AppTooltipLayer', () => {
  let wrapper

  afterEach(() => {
    wrapper?.unmount()
    document.body.innerHTML = ''
  })

  it('explica controles de solo icono al recibir foco y se cierra con Escape', async () => {
    wrapper = mount({
      components: { AppTooltipLayer },
      template: `
        <div>
          <AppTooltipLayer />
          <button type="button" aria-label="Editar alumno"><svg aria-hidden="true" /></button>
        </div>
      `,
    }, {
      attachTo: document.body,
      global: { stubs: { Teleport: true } },
    })

    const button = wrapper.get('button')
    button.element.focus()
    await button.trigger('focusin')
    await nextTick()

    expect(wrapper.get('[role="tooltip"]').text()).toBe('Editar alumno')
    expect(button.attributes('aria-describedby')).toContain('app-global-tooltip')

    await button.trigger('keydown', { key: 'Escape' })
    expect(wrapper.find('[role="tooltip"]').exists()).toBe(false)
    expect(button.attributes('aria-describedby')).toBeUndefined()
  })

  it('permite excluir un control cuyo nombre accesible ya es suficiente', async () => {
    wrapper = mount({
      components: { AppTooltipLayer },
      template: `
        <div>
          <AppTooltipLayer />
          <button type="button" aria-label="Más opciones" data-tooltip-disabled="true"><svg aria-hidden="true" /></button>
        </div>
      `,
    }, {
      attachTo: document.body,
      global: { stubs: { Teleport: true } },
    })

    const button = wrapper.get('button')
    await button.trigger('focusin')
    await nextTick()

    expect(wrapper.find('[role="tooltip"]').exists()).toBe(false)
    expect(button.attributes('aria-describedby')).toBeUndefined()
  })
})
