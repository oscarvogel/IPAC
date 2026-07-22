// Sistema global de toasts. Estado singleton a nivel de modulo.

import { ref, readonly } from 'vue'

const messages = ref([])
let nextId = 1

function push(text, { type = 'info', duration = 4000 } = {}) {
  const id = nextId++
  messages.value.push({ id, text, type })
  if (duration > 0) {
    setTimeout(() => {
      dismiss(id)
    }, duration)
  }
  return id
}

function dismiss(id) {
  messages.value = messages.value.filter((m) => m.id !== id)
}

function success(text, opts = {}) {
  return push(text, { ...opts, type: 'success' })
}

function error(text, opts = {}) {
  return push(text, { ...opts, type: 'error' })
}

function info(text, opts = {}) {
  return push(text, { ...opts, type: 'info' })
}

export function useToast() {
  return {
    messages: readonly(messages),
    push,
    dismiss,
    success,
    error,
    info,
  }
}
