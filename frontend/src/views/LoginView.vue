<template>
  <MobileLogin
    v-if="isMobile"
    :loading="loading"
    :error-message="localError"
    @submit="handleSubmit"
  />
  <DesktopLogin
    v-else
    :loading="loading"
    :error-message="localError"
    @submit="handleSubmit"
  />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DesktopLogin from '@/components/auth/DesktopLogin.vue'
import MobileLogin from '@/components/auth/MobileLogin.vue'
import { useAuth } from '@/composables/useAuth'
import { useToast } from '@/composables/useToast'

const MOBILE_QUERY = '(max-width: 767px)'

const router = useRouter()
const { login, user, loading, error: authError } = useAuth()
const toast = useToast()
const localError = ref('')
const mediaQuery = window.matchMedia(MOBILE_QUERY)
const isMobile = ref(mediaQuery.matches)

function syncViewport(event) {
  isMobile.value = event.matches
  localError.value = ''
}

onMounted(() => {
  mediaQuery.addEventListener('change', syncViewport)
})

onBeforeUnmount(() => {
  mediaQuery.removeEventListener('change', syncViewport)
})

async function handleSubmit({ username, password, remember }) {
  localError.value = ''
  const ok = await login(username, password, { remember })
  if (ok) {
    router.replace(user.value?.perfil?.debe_cambiar_clave ? '/cambiar-clave' : '/dashboard')
    return
  }

  localError.value = authError.value || 'No se pudo iniciar sesión.'
  toast.error(localError.value)
}
</script>
