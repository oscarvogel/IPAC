const focusTrapState = new WeakMap()
const formValidationState = new WeakMap()

const focusableSelector = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

function visibleFocusableElements(element) {
  return [...element.querySelectorAll(focusableSelector)].filter((node) => (
    !node.hidden && node.getAttribute('aria-hidden') !== 'true'
  ))
}

export const vFocusTrap = {
  mounted(element, binding) {
    const state = {
      value: binding.value || {},
      previousFocus: document.activeElement,
      keydown: null,
    }

    state.keydown = (event) => {
      if (event.key === 'Escape') {
        if (!state.value.busy) state.value.close?.()
        return
      }

      if (event.key !== 'Tab') return
      const focusable = visibleFocusableElements(element)
      if (!focusable.length) {
        event.preventDefault()
        element.focus()
        return
      }

      const first = focusable[0]
      const last = focusable.at(-1)
      if (event.shiftKey && (document.activeElement === first || !element.contains(document.activeElement))) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    focusTrapState.set(element, state)
    element.addEventListener('keydown', state.keydown)

    requestAnimationFrame(() => {
      const initial = element.querySelector('[autofocus], input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled])')
        || visibleFocusableElements(element)[0]
      initial?.focus()
    })
  },

  updated(element, binding) {
    const state = focusTrapState.get(element)
    if (state) state.value = binding.value || {}
  },

  beforeUnmount(element) {
    const state = focusTrapState.get(element)
    if (!state) return
    element.removeEventListener('keydown', state.keydown)
    state.previousFocus?.focus?.()
    focusTrapState.delete(element)
  },
}

function validationMessage(control) {
  const validity = control.validity
  if (validity.valueMissing) return 'Este campo es obligatorio.'
  if (validity.typeMismatch && control.type === 'email') return 'Ingresá un email válido.'
  if (validity.rangeUnderflow) return `El valor mínimo es ${control.min}.`
  if (validity.rangeOverflow) return `El valor máximo es ${control.max}.`
  if (validity.tooLong) return `Usá como máximo ${control.maxLength} caracteres.`
  if (validity.patternMismatch) return 'Revisá el formato ingresado.'
  if (validity.badInput) return 'Ingresá un valor válido.'
  return control.validationMessage || 'Revisá este campo.'
}

function feedbackId(control) {
  if (!control.dataset.feedbackId) {
    const suffix = Math.random().toString(36).slice(2, 8)
    control.dataset.feedbackId = `${control.name || control.id || 'field'}-feedback-${suffix}`
  }
  return control.dataset.feedbackId
}

function validationContainer(control) {
  return control.closest('label') || control.parentElement
}

function clearValidation(control) {
  control.removeAttribute('aria-invalid')
  const id = control.dataset.feedbackId
  if (!id) return
  const feedback = document.getElementById(id)
  if (feedback && validationContainer(control)?.contains(feedback)) feedback.remove()
  const describedBy = (control.getAttribute('aria-describedby') || '')
    .split(/\s+/)
    .filter(Boolean)
    .filter((item) => item !== id)
  if (describedBy.length) control.setAttribute('aria-describedby', describedBy.join(' '))
  else control.removeAttribute('aria-describedby')
}

function showValidation(control) {
  if (!(control instanceof HTMLInputElement || control instanceof HTMLSelectElement || control instanceof HTMLTextAreaElement)) return
  if (control.disabled || control.validity.valid) {
    clearValidation(control)
    return
  }

  const id = feedbackId(control)
  const container = validationContainer(control)
  let feedback = document.getElementById(id)
  if (feedback && !container?.contains(feedback)) feedback = null
  if (!feedback) {
    feedback = document.createElement('small')
    feedback.id = id
    feedback.className = 'field-validation-message'
    feedback.setAttribute('role', 'alert')
    container?.append(feedback)
  }
  feedback.textContent = validationMessage(control)
  control.setAttribute('aria-invalid', 'true')
  const describedBy = new Set((control.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean))
  describedBy.add(id)
  control.setAttribute('aria-describedby', [...describedBy].join(' '))
}

export const vFormValidation = {
  mounted(form) {
    const onInvalid = (event) => {
      event.target.dataset.validationTouched = 'true'
      showValidation(event.target)
    }
    const onFocusOut = (event) => {
      const control = event.target
      if (!control.matches?.('input, select, textarea')) return
      control.dataset.validationTouched = 'true'
      showValidation(control)
    }
    const onInput = (event) => {
      const control = event.target
      if (control.dataset.validationTouched === 'true') showValidation(control)
    }

    form.addEventListener('invalid', onInvalid, true)
    form.addEventListener('focusout', onFocusOut)
    form.addEventListener('input', onInput)
    form.addEventListener('change', onInput)
    formValidationState.set(form, { onInvalid, onFocusOut, onInput })
  },

  beforeUnmount(form) {
    const state = formValidationState.get(form)
    if (!state) return
    form.removeEventListener('invalid', state.onInvalid, true)
    form.removeEventListener('focusout', state.onFocusOut)
    form.removeEventListener('input', state.onInput)
    form.removeEventListener('change', state.onInput)
    formValidationState.delete(form)
  },
}
