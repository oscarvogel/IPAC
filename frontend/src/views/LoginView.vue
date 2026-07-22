<template>
  <main class="login-screen">
    <div class="login-panel">
      <div class="login-copy">
        <span class="brand-mark">IP</span>
        <p class="eyebrow">IPAC CRM</p>
        <h1>Administracion y cobranzas en una sola vista.</h1>
        <p>Un panel para encontrar alumnos, revisar sucursal, cargar datos y preparar el flujo de caja sin perder contexto.</p>
      </div>

      <form class="login-card" @submit.prevent="handleSubmit">
        <h2>Ingresar</h2>
        <label>
          Usuario
          <input v-model="form.username" autocomplete="username" required />
        </label>
        <label>
          Clave
          <input v-model="form.password" type="password" autocomplete="current-password" required />
        </label>
        <p v-if="localError" class="alert">{{ localError }}</p>
        <button class="primary-button" type="submit" :disabled="loading">
          {{ loading ? 'Ingresando...' : 'Entrar al CRM' }}
        </button>
      </form>
    </div>
  </main>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { login, loading, error: authError } = useAuth()
const toast = useToast()

const form = reactive({ username: '', password: '' })
const localError = ref('')

async function handleSubmit() {
  localError.value = ''
  const ok = await login(form.username, form.password)
  if (ok) {
    router.replace('/alumnos')
  } else {
    localError.value = authError.value || 'No se pudo iniciar sesion.'
    toast.error(localError.value)
  }
}
</script>
