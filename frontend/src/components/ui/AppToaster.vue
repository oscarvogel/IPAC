<template>
  <Teleport to="body">
    <div class="app-toaster" aria-label="Notificaciones">
      <TransitionGroup name="toast-stack">
        <article
          v-for="message in messages"
          :key="message.id"
          :class="['toast-message', `toast-message-${message.type}`]"
          :role="message.type === 'error' ? 'alert' : 'status'"
          :aria-live="message.type === 'error' ? 'assertive' : 'polite'"
        >
          <span class="toast-message-icon">
            <component :is="iconFor(message.type)" aria-hidden="true" />
          </span>

          <span class="toast-message-copy">
            <strong>{{ message.title }}</strong>
            <span>{{ message.text }}</span>
          </span>

          <button
            type="button"
            class="toast-message-close"
            :aria-label="`Cerrar notificación: ${message.text}`"
            @click="dismiss(message.id)"
          >
            <XMarkIcon aria-hidden="true" />
          </button>

          <span
            v-if="message.duration > 0"
            class="toast-message-progress"
            :style="{ '--toast-duration': `${message.duration}ms` }"
            aria-hidden="true"
          />
        </article>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { useToast } from '@/composables/useToast'

const { messages, dismiss } = useToast()

function iconFor(type) {
  const icons = {
    success: CheckCircleIcon,
    error: ExclamationCircleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon,
  }
  return icons[type] || InformationCircleIcon
}
</script>
