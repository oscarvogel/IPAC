<template>
  <section
    class="app-page-state"
    :class="{ 'is-loading': loading }"
    :aria-busy="loading"
    :aria-label="loading ? `Cargando ${label}` : undefined"
  >
    <template v-if="loading">
      <span class="sr-only">Cargando {{ label }}…</span>
      <div class="page-state-metrics" aria-hidden="true">
        <span v-for="item in 4" :key="item" class="page-state-metric">
          <i />
          <span><b /><b /><b /></span>
        </span>
      </div>
      <div class="page-state-toolbar" aria-hidden="true">
        <span><b /><b /></span>
        <i />
      </div>
      <div class="page-state-content" aria-hidden="true">
        <span v-for="row in 5" :key="row">
          <b /><b /><b /><b />
        </span>
      </div>
    </template>

    <div v-else class="page-state-error" role="alert">
      <span><ExclamationTriangleIcon aria-hidden="true" /></span>
      <p class="eyebrow">No se pudo cargar {{ label }}</p>
      <h2>Algo interrumpió la conexión</h2>
      <p>{{ error || 'Revisá la conexión e intentá nuevamente.' }}</p>
      <button type="button" @click="$emit('retry')">
        <ArrowPathIcon aria-hidden="true" />
        <span>Reintentar</span>
      </button>
    </div>
  </section>
</template>

<script setup>
import { ArrowPathIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'

defineProps({
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  label: { type: String, default: 'la información' },
})

defineEmits(['retry'])
</script>
