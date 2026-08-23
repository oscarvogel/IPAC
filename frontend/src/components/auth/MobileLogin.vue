<template>
  <main class="mobile-login bg-background text-text-primary" aria-labelledby="mobile-login-title">
    <section class="mobile-login-intro bg-primary-hover text-surface" aria-label="IPAC CRM">
      <header class="mobile-login-brand">
        <img src="/logo-ipac.jpg" alt="" />
        <div>
          <strong>IPAC CRM</strong>
          <span>CRM administrativo</span>
        </div>
      </header>
      <div class="mobile-intro-copy">
        <p>Gestión simple, estés donde estés.</p>
        <span>Alumnos, cobranzas y caja en un solo lugar.</span>
      </div>
    </section>

    <section class="mobile-login-access bg-surface">
      <LoginThemeToggle />
      <div class="mobile-form-heading">
        <span class="mobile-form-icon bg-primary-soft text-primary">
          <AcademicCapIcon aria-hidden="true" />
        </span>
        <div>
          <p>Bienvenido</p>
          <h1 id="mobile-login-title">Ingresá a tu cuenta</h1>
        </div>
      </div>

      <form v-form-validation class="mobile-login-form" @submit.prevent="submitForm">
        <label class="mobile-field">
          <span>Usuario</span>
          <span class="mobile-input-wrap">
            <UserIcon aria-hidden="true" />
            <input
              v-model.trim="form.username"
              name="username"
              autocomplete="username"
              inputmode="text"
              placeholder="Tu usuario"
              required
            />
          </span>
        </label>

        <label class="mobile-field">
          <span>Clave</span>
          <span class="mobile-input-wrap">
            <LockClosedIcon aria-hidden="true" />
            <input
              v-model="form.password"
              name="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="Tu clave"
              required
            />
            <button
              class="mobile-password-toggle"
              type="button"
              :aria-label="showPassword ? 'Ocultar clave' : 'Mostrar clave'"
              @click="showPassword = !showPassword"
            >
              <EyeSlashIcon v-if="showPassword" aria-hidden="true" />
              <EyeIcon v-else aria-hidden="true" />
            </button>
          </span>
        </label>

        <label class="mobile-remember">
          <input v-model="form.remember" type="checkbox" />
          <span>Mantener mi sesión iniciada</span>
        </label>

        <p v-if="errorMessage" class="login-form-error" role="alert">
          {{ errorMessage }}
        </p>

        <button
          class="mobile-submit bg-primary hover:bg-primary-hover"
          type="submit"
          :disabled="loading"
        >
          <AppButtonContent :loading="loading" label="Ingresar" loading-label="Ingresando…" />
        </button>
      </form>

      <aside class="mobile-login-help border-border bg-primary-soft" aria-label="Ayuda">
        <div class="mobile-help-heading">
          <ChatBubbleLeftRightIcon aria-hidden="true" />
          <div>
            <strong>¿Necesitás ayuda?</strong>
            <span>Nuestro equipo puede ayudarte.</span>
          </div>
        </div>
        <div class="mobile-help-links">
          <a href="mailto:soporte@ipac.edu.ar">
            <EnvelopeIcon aria-hidden="true" />
            soporte@ipac.edu.ar
          </a>
          <a href="tel:+543743123456">
            <PhoneIcon aria-hidden="true" />
            +54 3743 123456
          </a>
        </div>
      </aside>
    </section>
  </main>
</template>

<script setup>
import { reactive, ref } from 'vue'
import {
  AcademicCapIcon,
  ChatBubbleLeftRightIcon,
  EnvelopeIcon,
  EyeIcon,
  EyeSlashIcon,
  LockClosedIcon,
  PhoneIcon,
  UserIcon,
} from '@heroicons/vue/24/outline'
import AppButtonContent from '@/components/ui/AppButtonContent.vue'
import LoginThemeToggle from '@/components/auth/LoginThemeToggle.vue'
import { vFormValidation } from '@/directives/accessibility'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  errorMessage: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['submit'])
const showPassword = ref(false)
const form = reactive({
  username: '',
  password: '',
  remember: false,
})

function submitForm() {
  if (props.loading) return
  emit('submit', { ...form })
}
</script>
