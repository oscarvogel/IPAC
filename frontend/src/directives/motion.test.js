import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { vRevealOnScroll } from './motion'

function mountReveal() {
  return mount({
    template: '<section v-reveal-on-scroll>Contenido</section>',
  }, {
    global: { directives: { revealOnScroll: vRevealOnScroll } },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('directiva de reveal al hacer scroll', () => {
  it('muestra el contenido inmediatamente cuando no hay IntersectionObserver', () => {
    const wrapper = mountReveal()

    expect(wrapper.get('section').classes()).toEqual(['reveal-on-scroll', 'is-visible'])
  })

  it('muestra el contenido al entrar al viewport y deja de observarlo', () => {
    let callback
    const observer = {
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn(),
    }
    class MockIntersectionObserver {
      constructor(handler) {
        callback = handler
      }

      observe = observer.observe
      unobserve = observer.unobserve
      disconnect = observer.disconnect
    }

    vi.stubGlobal('IntersectionObserver', MockIntersectionObserver)
    const wrapper = mountReveal()
    const element = wrapper.get('section')

    expect(observer.observe).toHaveBeenCalledWith(element.element)
    expect(element.classes()).not.toContain('is-visible')

    callback([{ isIntersecting: true }])

    expect(element.classes()).toContain('is-visible')
    expect(observer.unobserve).toHaveBeenCalledWith(element.element)
    wrapper.unmount()
  })

  it('omite la animacion cuando el usuario prefiere movimiento reducido', () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })))
    vi.stubGlobal('IntersectionObserver', class {})
    const wrapper = mountReveal()

    expect(wrapper.get('section').classes()).toContain('is-visible')
  })
})
