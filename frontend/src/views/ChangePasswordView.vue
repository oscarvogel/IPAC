<template>
  <main class="change-password-screen" aria-labelledby="change-password-title">
    <section class="change-password-card" aria-describedby="change-password-description">
      <div class="change-password-brand" aria-label="IPAC CRM">
        <img src="/logo-ipac.jpg" alt="IPAC" />
        <span>IPAC CRM administrativo</span>
      </div>
      <p class="eyebrow">Seguridad de la cuenta</p>
      <h1 id="change-password-title">Cambiá tu clave para continuar</h1>
      <p id="change-password-description">
        La clave que recibiste es temporal. Elegí una nueva clave personal antes de acceder al sistema.
      </p>

      <form @submit.prevent="submitForm" novalidate>
        <label>
          Nueva clave
          <input
            v-model="form.newPassword"
            name="new_password"
            type="password"
            autocomplete="new-password"
            minlength="8"
            required
          />
        </label>
        <label>
          Repetir nueva clave
          <input
            v-model="form.confirmation"
            name="new_password_confirmation"
            type="password"
            autocomplete="new-password"
            minlength="8"
            required
          />
        </label>
        <p v-if="formError" class="change-password-error" role="alert">{{ formError }}</p>
        <button class="primary-button" type="submit" :disabled="loading">
          {{ loading ? 'Guardando…' : 'Guardar nueva clave' }}
        </button>
      </form>
    </section>
  </main>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { changePassword, loading, error } = useAuth()
const form = reactive({ newPassword: '', confirmation: '' })
const localError = ref('')
const formError = computed(() => localError.value || error.value)

async function submitForm() {
  localError.value = ''
  if (form.newPassword.length < 8) {
    localError.value = 'La nueva clave debe tener al menos 8 caracteres.'
    return
  }
  if (form.newPassword !== form.confirmation) {
    localError.value = 'Las claves no coinciden.'
    return
  }
  if (await changePassword(form.newPassword, form.confirmation)) {
    router.push('/dashboard')
  }
}
</script>

<style scoped>
.change-password-screen {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: var(--background, #f5f7fb);
  color: var(--text-primary, #172033);
}

.change-password-card {
  width: min(100%, 480px);
  padding: 36px;
  border: 1px solid var(--border, #dfe5ef);
  border-radius: 22px;
  background: var(--surface, #fff);
  box-shadow: 0 20px 60px rgb(23 32 51 / 12%);
}

.change-password-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 34px;
  color: var(--primary, #2457c5);
  font-weight: 700;
}

.change-password-brand img { width: 34px; height: 34px; }
.change-password-card h1 { margin: 6px 0 12px; font-size: clamp(1.7rem, 4vw, 2.2rem); }
.change-password-card > p:not(.eyebrow) { color: var(--text-secondary, #667085); line-height: 1.55; }
.change-password-card form { display: grid; gap: 18px; margin-top: 28px; }
.change-password-card label { display: grid; gap: 7px; font-weight: 600; }
.change-password-card input { width: 100%; }
.change-password-card button { width: 100%; margin-top: 4px; }
.change-password-error { margin: 0; color: #b42318; font-size: 0.92rem; }

@media (max-width: 520px) {
  .change-password-card { padding: 26px 22px; }
}
</style>
