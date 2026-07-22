<template>
  <Teleport to="body">
    <div v-if="messages.length" class="app-toaster" role="status" aria-live="polite">
      <button
        v-for="msg in messages"
        :key="msg.id"
        :class="['toast', `toast-${msg.type}`]"
        type="button"
        @click="dismiss(msg.id)"
      >
        {{ msg.text }}
      </button>
    </div>
  </Teleport>
</template>

<script setup>
import { useToast } from '@/composables/useToast'

const { messages, dismiss } = useToast()
</script>

<style scoped>
.app-toaster {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 360px;
  pointer-events: none;
}

.toast {
  pointer-events: auto;
  padding: 0.75rem 1rem;
  border: 0;
  border-radius: 8px;
  background: #1f2030;
  color: #fff;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
  cursor: pointer;
  font: inherit;
  font-size: 0.875rem;
  text-align: left;
  line-height: 1.4;
}

.toast-success {
  background: #1f7a4d;
}

.toast-error {
  background: #a8313a;
}

.toast-info {
  background: #2c4f9c;
}
</style>
