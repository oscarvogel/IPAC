import { prefersReducedMotion } from '@/lib/motion'

const revealObservers = new WeakMap()

function reveal(element) {
  element.classList.add('is-visible')
}

export const vRevealOnScroll = {
  mounted(element) {
    element.classList.add('reveal-on-scroll')

    if (prefersReducedMotion() || !('IntersectionObserver' in window)) {
      reveal(element)
      return
    }

    const observer = new IntersectionObserver(([entry]) => {
      if (!entry?.isIntersecting) return
      reveal(element)
      observer.unobserve(element)
      revealObservers.delete(element)
    }, {
      threshold: 0.12,
      rootMargin: '0px 0px -8% 0px',
    })

    revealObservers.set(element, observer)
    observer.observe(element)
  },

  beforeUnmount(element) {
    revealObservers.get(element)?.disconnect()
    revealObservers.delete(element)
  },
}
