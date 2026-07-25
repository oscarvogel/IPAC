<template>
  <header class="topbar">
    <div>
      <p class="eyebrow">Panel de trabajo</p>
      <h1>{{ title }}</h1>
    </div>
    <div v-if="actions.length" class="top-actions">
      <button
        v-for="action in actions"
        :key="action.label"
        :class="action.variant === 'primary' ? 'new-button' : 'secondary-button'"
        type="button"
        :disabled="action.disabled"
        @click="action.onClick"
      >
        {{ action.label }}
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTopbarActions } from '@/composables/useTopbarActions'

const route = useRoute()
const { actions: providedActions } = useTopbarActions()

const titles = {
  '/dashboard': 'Dashboard',
  '/alumnos': 'Alumnos',
  '/caja': 'Caja',
  '/conceptos': 'Conceptos',
  '/reportes': 'Reportes',
  '/sucursales': 'Sucursales',
}

const title = computed(() => titles[route.path] || 'IPAC')
const actions = computed(() => providedActions.value || [])
</script>
