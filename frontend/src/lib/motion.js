import { gsap } from 'gsap'
import { Flip } from 'gsap/Flip'

gsap.registerPlugin(Flip)

export const MOTION_DURATIONS = Object.freeze({
  fast: 0.16,
  standard: 0.22,
  emphasis: 0.32,
})

export const THEME_COLOR_VARIABLES = Object.freeze([
  '--primary',
  '--primary-hover',
  '--primary-soft',
  '--on-primary',
  '--secondary',
  '--secondary-hover',
  '--secondary-soft',
  '--on-secondary',
  '--background',
  '--surface',
  '--surface-soft',
  '--text-primary',
  '--text-secondary',
  '--text-muted',
  '--border',
  '--row-hover',
  '--success',
  '--warning',
  '--danger',
  '--info',
  '--hero-muted',
  '--hero-accent',
  '--nav',
  '--nav-hover',
  '--nav-text',
  '--nav-text-active',
])

export function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true
}

export function readThemeVariables(
  root = typeof document !== 'undefined' ? document.documentElement : null,
) {
  if (!root || typeof getComputedStyle !== 'function') return {}
  const styles = getComputedStyle(root)
  return Object.fromEntries(
    THEME_COLOR_VARIABLES
      .map((name) => [name, styles.getPropertyValue(name).trim()])
      .filter(([, value]) => value),
  )
}

let activeThemeTween = null
let activeThemeRoot = null

export function animateThemeTransition(root, fromValues, toValues, {
  duration = MOTION_DURATIONS.emphasis,
  onComplete,
} = {}) {
  if (!root) {
    onComplete?.()
    return null
  }

  activeThemeTween?.kill()
  activeThemeRoot?.classList.remove('theme-transition-active')
  activeThemeTween = null
  activeThemeRoot = null

  const from = Object.fromEntries(
    THEME_COLOR_VARIABLES
      .map((name) => [name, fromValues?.[name]])
      .filter(([, value]) => value),
  )
  const to = Object.fromEntries(
    THEME_COLOR_VARIABLES
      .map((name) => [name, toValues?.[name]])
      .filter(([, value]) => value),
  )

  if (!Object.keys(to).length) {
    onComplete?.()
    return null
  }

  const clearThemeVariables = () => gsap.set(root, {
    clearProps: THEME_COLOR_VARIABLES.join(','),
  })

  if (prefersReducedMotion()) {
    gsap.set(root, to)
    clearThemeVariables()
    onComplete?.()
    return null
  }

  gsap.set(root, from)
  root.classList.add('theme-transition-active')
  activeThemeRoot = root
  activeThemeTween = gsap.to(root, {
    ...to,
    duration,
    ease: 'power2.inOut',
    onComplete: () => {
      clearThemeVariables()
      root.classList.remove('theme-transition-active')
      activeThemeTween = null
      activeThemeRoot = null
      onComplete?.()
    },
  })
  return activeThemeTween
}

export function createMotionContext(scope, callback) {
  const context = gsap.context(callback, scope)
  return () => context.revert()
}

function toElements(targets) {
  return Array.from(targets || []).filter(Boolean)
}

function completeImmediately(targets, onComplete) {
  const elements = toElements(targets)
  if (elements.length) gsap.set(elements, { clearProps: 'transform,opacity,visibility' })
  onComplete?.()
  return null
}

export function animateStaggerIn(targets, {
  duration = MOTION_DURATIONS.standard,
  stagger = 0.05,
  y = 10,
  onComplete,
} = {}) {
  const elements = toElements(targets)
  if (!elements.length || prefersReducedMotion()) return completeImmediately(elements, onComplete)

  return gsap.fromTo(
    elements,
    { autoAlpha: 0, y },
    {
      autoAlpha: 1,
      y: 0,
      duration,
      ease: 'power2.out',
      stagger,
      onComplete,
    },
  )
}

export function animateSectionEnter(root, done) {
  const children = root ? Array.from(root.children) : []
  return animateStaggerIn(children.length ? children : [root], {
    stagger: 0.05,
    onComplete: done,
  })
}

export function animateSectionLeave(root, done) {
  if (!root || prefersReducedMotion()) return completeImmediately(root, done)

  return gsap.to(root, {
    autoAlpha: 0,
    y: -4,
    duration: MOTION_DURATIONS.fast,
    ease: 'power1.in',
    onComplete: done,
  })
}

export function animateProgressBars(targets, {
  duration = MOTION_DURATIONS.emphasis,
  stagger = 0.04,
} = {}) {
  const elements = toElements(targets)
  if (!elements.length || prefersReducedMotion()) return completeImmediately(elements)

  return gsap.fromTo(
    elements,
    { scaleX: 0 },
    {
      scaleX: 1,
      duration,
      ease: 'power2.out',
      stagger,
      transformOrigin: 'left center',
    },
  )
}

export function animateCounter(target, from, to, {
  duration = MOTION_DURATIONS.emphasis,
  format = (value) => String(Math.round(value)),
  onUpdate,
  onComplete,
} = {}) {
  if (!target) {
    onComplete?.()
    return null
  }

  const start = Number.isFinite(Number(from)) ? Number(from) : 0
  const finish = Number.isFinite(Number(to)) ? Number(to) : 0

  if (prefersReducedMotion()) {
    target.textContent = format(finish)
    onComplete?.()
    return null
  }

  const state = { value: start }
  target.textContent = format(start)
  return gsap.to(state, {
    value: finish,
    duration,
    ease: 'power2.out',
    onUpdate: () => {
      target.textContent = format(state.value)
      onUpdate?.(state.value)
    },
    onComplete: () => {
      target.textContent = format(finish)
      onComplete?.()
    },
  })
}

function dialogPanel(root) {
  return root?.querySelector('[data-motion-panel], .modal-card, .confirm-dialog-card')
}

export function animateDialogEnter(root, done) {
  const panel = dialogPanel(root)
  if (prefersReducedMotion()) return completeImmediately([root, panel], done)

  return gsap.timeline({ onComplete: done })
    .fromTo(root, { autoAlpha: 0 }, { autoAlpha: 1, duration: MOTION_DURATIONS.fast, ease: 'power1.out' })
    .fromTo(
      panel,
      { autoAlpha: 0, y: 8, scale: 0.98 },
      { autoAlpha: 1, y: 0, scale: 1, duration: MOTION_DURATIONS.standard, ease: 'power2.out' },
      0,
    )
}

export function animateDialogLeave(root, done) {
  const panel = dialogPanel(root)
  if (prefersReducedMotion()) return completeImmediately([root, panel], done)

  return gsap.timeline({ onComplete: done })
    .to(panel, { autoAlpha: 0, y: 8, scale: 0.98, duration: MOTION_DURATIONS.fast, ease: 'power1.in' })
    .to(root, { autoAlpha: 0, duration: MOTION_DURATIONS.fast, ease: 'power1.in' }, 0)
}

export function animateSidebar(sidebar, backdrop, open, onComplete) {
  if (!sidebar) {
    onComplete?.()
    return null
  }

  if (prefersReducedMotion()) {
    gsap.set(sidebar, { xPercent: open ? 0 : -105, clearProps: 'transform' })
    if (backdrop) gsap.set(backdrop, { autoAlpha: open ? 1 : 0, clearProps: 'opacity,visibility' })
    onComplete?.()
    return null
  }

  if (open) {
    gsap.set(sidebar, { xPercent: -105 })
    if (backdrop) gsap.set(backdrop, { autoAlpha: 0 })
    return gsap.timeline({ onComplete })
      .to(sidebar, { xPercent: 0, duration: MOTION_DURATIONS.standard, ease: 'power2.out' })
      .to(backdrop, { autoAlpha: 1, duration: MOTION_DURATIONS.standard, ease: 'power1.out' }, 0.04)
  }

  gsap.set(sidebar, { xPercent: 0 })
  return gsap.timeline({ onComplete })
    .to(sidebar, { xPercent: -105, duration: MOTION_DURATIONS.fast, ease: 'power1.in' })
    .to(backdrop, { autoAlpha: 0, duration: MOTION_DURATIONS.fast, ease: 'power1.in' }, 0)
}

export function animateListEnter(element, done) {
  if (prefersReducedMotion()) return completeImmediately(element, done)

  return gsap.fromTo(
    element,
    { autoAlpha: 0, y: 6 },
    { autoAlpha: 1, y: 0, duration: MOTION_DURATIONS.standard, ease: 'power2.out', onComplete: done },
  )
}

export function animateListLeave(element, done) {
  if (prefersReducedMotion()) return completeImmediately(element, done)

  return gsap.to(element, {
    autoAlpha: 0,
    y: -4,
    duration: MOTION_DURATIONS.fast,
    ease: 'power1.in',
    onComplete: done,
  })
}

export function animateToastEnter(element, done) {
  if (prefersReducedMotion()) return completeImmediately(element, done)

  const timeline = gsap.timeline({ onComplete: done })
    .fromTo(
      element,
      { autoAlpha: 0, x: 22, scale: 0.98 },
      { autoAlpha: 1, x: 0, scale: 1, duration: MOTION_DURATIONS.standard, ease: 'power2.out' },
    )
  const successIcon = element.classList.contains('toast-message-success')
    ? element.querySelector('.toast-message-icon')
    : null
  if (successIcon) {
    timeline.fromTo(
      successIcon,
      { scale: 0.72, rotate: -8 },
      { scale: 1, rotate: 0, duration: MOTION_DURATIONS.fast, ease: 'back.out(1.7)' },
      0.05,
    )
  }
  return timeline
}

export function animateToastLeave(element, done) {
  if (prefersReducedMotion()) return completeImmediately(element, done)

  return gsap.to(element, {
    autoAlpha: 0,
    x: 22,
    scale: 0.98,
    duration: MOTION_DURATIONS.fast,
    ease: 'power1.in',
    onComplete: done,
  })
}

export function captureFlipState(elements) {
  const targets = toElements(elements)
  if (prefersReducedMotion() || !targets.length) return null
  return Flip.getState(targets)
}

export function animateFlipState(state, elements) {
  const targets = toElements(elements)
  if (!state || prefersReducedMotion() || !targets.length) return null

  return Flip.from(state, {
    targets,
    duration: MOTION_DURATIONS.standard,
    ease: 'power2.out',
    absolute: false,
    nested: true,
    prune: true,
  })
}
