<template>
  <Teleport to="body">
    <Transition name="confirm-dialog">
      <div
        v-if="open"
        class="confirm-dialog-backdrop"
        @click.self="cancel"
      >
        <section
          v-focus-trap="{ close: cancel, busy: loading }"
          class="confirm-dialog-card"
          :class="`tone-${tone}`"
          role="alertdialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          :aria-describedby="descriptionId"
        >
          <span class="confirm-dialog-icon">
            <ExclamationTriangleIcon aria-hidden="true" />
          </span>

          <div class="confirm-dialog-copy">
            <p class="eyebrow">Confirmación requerida</p>
            <h2 :id="titleId">{{ title }}</h2>
            <p :id="descriptionId">{{ description }}</p>
            <strong v-if="subject">{{ subject }}</strong>
          </div>

          <div class="confirm-dialog-actions">
            <button type="button" class="confirm-cancel" :disabled="loading" @click="cancel">
              Cancelar
            </button>
            <button type="button" class="confirm-submit" :disabled="loading" @click="$emit('confirm')">
              <ArrowPathIcon v-if="loading" class="is-spinning" aria-hidden="true" />
              <NoSymbolIcon v-else aria-hidden="true" />
              <span>{{ loading ? 'Procesando' : confirmLabel }}</span>
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import {
  ArrowPathIcon,
  ExclamationTriangleIcon,
  NoSymbolIcon,
} from '@heroicons/vue/24/outline'
import { vFocusTrap } from '@/directives/accessibility'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, required: true },
  description: { type: String, required: true },
  subject: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Confirmar' },
  tone: { type: String, default: 'danger' },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['cancel', 'confirm'])
const titleId = `confirm-title-${Math.random().toString(36).slice(2, 8)}`
const descriptionId = `confirm-description-${Math.random().toString(36).slice(2, 8)}`

function cancel() {
  if (props.loading) return
  emit('cancel')
}
</script>
