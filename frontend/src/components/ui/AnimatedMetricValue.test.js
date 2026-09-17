import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import AnimatedMetricValue from './AnimatedMetricValue.vue'

describe('AnimatedMetricValue', () => {
  it('expone el valor monetario final de forma accesible', async () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })))
    const wrapper = mount(AnimatedMetricValue, {
      props: { value: 32000, kind: 'money', prefix: '$ ' },
    })
    await flushPromises()

    expect(wrapper.get('.sr-only').text()).toBe('$ 32.000,00')
    expect(wrapper.get('strong').attributes('aria-hidden')).toBeUndefined()
  })
})
