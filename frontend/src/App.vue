<template>
  <AppToaster />
  <RouterView />
</template>

<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import AppToaster from '@/components/ui/AppToaster.vue'

const { fetchCurrentUser } = useAuth()

// Si hay token en localStorage, intentamos hidratar el usuario.
// Si el token es invalido, fetchCurrentUser lo limpia y el guard
// redirige al login en la proxima navegacion.
onMounted(() => {
  fetchCurrentUser()
})
</script>
