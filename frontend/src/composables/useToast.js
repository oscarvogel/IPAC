// Sistema global de toasts. Estado singleton a nivel de modulo.

import { ref, readonly } from 'vue'

const messages = ref([])
let nextId = 1
const timers = new Map()

const defaultTitles = {
  success: 'Operación completada',
  error: 'No pudimos completar la acción',
  warning: 'Revisá esta información',
  info: 'Información',
}

function push(text, { type = 'info', duration = 4500, title = '' } = {}) {
  const duplicate = messages.value.find((message) => (
    message.text === text && message.type === type
  ))
  if (duplicate) dismiss(duplicate.id)

  const id = nextId++
  messages.value.push({
    id,
    text,
    type,
    title: title || defaultTitles[type] || defaultTitles.info,
    duration,
  })

  if (messages.value.length > 4) dismiss(messages.value[0].id)

  if (duration > 0) {
    const timer = setTimeout(() => {
      dismiss(id)
    }, duration)
    timers.set(id, timer)
  }
  return id
}

function dismiss(id) {
  if (timers.has(id)) {
    clearTimeout(timers.get(id))
    timers.delete(id)
  }
  messages.value = messages.value.filter((m) => m.id !== id)
}

function clearAll() {
  timers.forEach((timer) => clearTimeout(timer))
  timers.clear()
  messages.value = []
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

function warning(text, opts = {}) {
  return push(text, { ...opts, type: 'warning' })
}

export function useToast() {
  return {
    messages: readonly(messages),
    push,
    dismiss,
    clearAll,
    success,
    error,
    info,
    warning,
  }
}
