<template>
  <span class="app-button-content">
    <ArrowPathIcon v-if="loading" class="is-spinning" aria-hidden="true" />
    <slot v-else name="icon" />
    <span>{{ loading ? loadingLabel : label }}</span>
  </span>
</template>

<script setup>
import { ArrowPathIcon } from '@heroicons/vue/24/outline'

defineProps({
  loading: { type: Boolean, default: false },
  label: { type: String, required: true },
  loadingLabel: { type: String, default: 'Procesando…' },
})
</script>
