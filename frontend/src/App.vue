<template>
  <AppToaster />
  <AppTooltipLayer />
  <AppLoadingScreen v-if="initializing" />
  <RouterView />
</template>

<script setup>
import { RouterView } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import AppToaster from '@/components/ui/AppToaster.vue'
import AppTooltipLayer from '@/components/ui/AppTooltipLayer.vue'
import AppLoadingScreen from '@/components/ui/AppLoadingScreen.vue'

const { fetchCurrentUser, initializing } = useAuth()

// Si hay token en localStorage, iniciamos la hidratacion antes del primer
// render para que la pantalla global cubra ese breve estado de arranque.
fetchCurrentUser()
</script>
