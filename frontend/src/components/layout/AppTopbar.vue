<template>
  <header class="topbar">
    <div>
      <p class="eyebrow">Panel de trabajo</p>
      <h1>{{ title }}</h1>
    </div>
    <div class="top-actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const titles = {
  '/alumnos': 'Alumnos',
  '/caja': 'Caja',
  '/conceptos': 'Conceptos',
  '/reportes': 'Reportes',
  '/sucursales': 'Sucursales',
}

const title = computed(() => titles[route.path] || 'IPAC')
</script>
