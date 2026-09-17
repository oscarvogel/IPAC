import { gsap } from 'gsap'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  animateThemeTransition,
  animateCounter,
  animateProgressBars,
  createMotionContext,
  MOTION_DURATIONS,
} from './motion'

afterEach(() => {
  gsap.killTweensOf('*')
  vi.unstubAllGlobals()
})

describe('utilidades de motion GSAP', () => {
  it('expone la escala de duraciones institucionales', () => {
    expect(MOTION_DURATIONS).toEqual({ fast: 0.16, standard: 0.22, emphasis: 0.32 })
  })

  it('actualiza un contador y conserva el formato final', () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false })))
    const target = document.createElement('span')
    const tween = animateCounter(target, 0, 1234.5, {
      duration: 0,
      format: (value) => Number(value).toFixed(2),
    })

    tween?.progress(1)

    expect(target.textContent).toBe('1234.50')
  })

  it('finaliza inmediatamente cuando se prefiere reducir movimiento', () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })))
    const target = document.createElement('span')
    const completed = vi.fn()

    const tween = animateCounter(target, 0, 42, { onComplete: completed })

    expect(tween).toBeNull()
    expect(target.textContent).toBe('42')
    expect(completed).toHaveBeenCalledTimes(1)
  })

  it('respeta estilos funcionales al desactivar la animación de barras', () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })))
    const target = document.createElement('span')
    target.style.width = '42%'

    animateProgressBars([target])

    expect(target.style.width).toBe('42%')
    expect(target.style.transform).toBe('')
  })

  it('interpola tokens de tema y limpia sus estilos al terminar', () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false })))
    const root = document.documentElement
    const tween = animateThemeTransition(
      root,
      { '--background': 'rgb(246, 248, 252)' },
      { '--background': 'rgb(11, 18, 32)' },
      { duration: 0 },
    )

    tween?.progress(1)

    expect(root.classList).not.toContain('theme-transition-active')
    expect(root.style.getPropertyValue('--background')).toBe('')
  })

  it('revierte tweens creados dentro de un contexto', () => {
    const scope = document.createElement('div')
    document.body.appendChild(scope)
    let tween
    const cleanup = createMotionContext(scope, () => {
      tween = gsap.to(scope, { x: 20, duration: 1 })
    })

    expect(gsap.getTweensOf(scope)).toContain(tween)
    cleanup()

    expect(gsap.getTweensOf(scope)).toHaveLength(0)
    scope.remove()
  })
})
