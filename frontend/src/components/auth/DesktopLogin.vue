<template>
  <main class="desktop-login bg-background text-text-primary" aria-labelledby="desktop-login-title">
    <section class="desktop-login-story bg-primary-hover text-surface" aria-label="IPAC CRM">
      <header class="desktop-login-brand">
        <img src="/logo-ipac.jpg" alt="" />
        <div>
          <strong>IPAC CRM</strong>
          <span>CRM administrativo</span>
        </div>
      </header>

      <div class="desktop-login-story-copy">
        <h1>Administración y cobranzas<br />en una sola vista.</h1>
        <p>
          IPAC CRM centraliza la gestión de alumnos, pagos, sucursales y caja
          para que tomes mejores decisiones y ahorres tiempo cada día.
        </p>
      </div>

      <div class="desktop-feature-grid">
        <article
          v-for="feature in features"
          :key="feature.title"
          class="desktop-feature-card border-info/50"
        >
          <span class="desktop-feature-icon bg-primary text-surface">
            <component :is="feature.icon" aria-hidden="true" />
          </span>
          <div>
            <h2>{{ feature.title }}</h2>
            <p>{{ feature.description }}</p>
          </div>
        </article>
      </div>
    </section>

    <section class="desktop-login-access bg-background">
      <LoginThemeToggle />
      <form v-form-validation class="desktop-login-form border-border bg-surface" @submit.prevent="submitForm">
        <div class="desktop-form-brand">
          <img src="/logo-ipac.jpg" alt="IPAC" />
          <span>IPAC CRM</span>
        </div>

        <h2 id="desktop-login-title">Ingresar</h2>

        <label class="desktop-field">
          <span>Usuario</span>
          <span class="desktop-input-wrap">
            <UserIcon aria-hidden="true" />
            <input
              v-model.trim="form.username"
              name="username"
              autocomplete="username"
              placeholder="Ingresa tu usuario"
              required
            />
          </span>
        </label>

        <label class="desktop-field">
          <span>Clave</span>
          <span class="desktop-input-wrap">
            <LockClosedIcon aria-hidden="true" />
            <input
              v-model="form.password"
              name="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="Ingresa tu clave"
              required
            />
            <button
              class="desktop-password-toggle"
              type="button"
              :aria-label="showPassword ? 'Ocultar clave' : 'Mostrar clave'"
              @click="showPassword = !showPassword"
            >
              <EyeSlashIcon v-if="showPassword" aria-hidden="true" />
              <EyeIcon v-else aria-hidden="true" />
            </button>
          </span>
        </label>

        <label class="desktop-remember">
          <input v-model="form.remember" type="checkbox" />
          <span>Recordarme</span>
        </label>

        <p v-if="errorMessage" class="login-form-error" role="alert">
          {{ errorMessage }}
        </p>

        <button
          class="desktop-submit bg-primary hover:bg-primary-hover"
          type="submit"
          :disabled="loading"
        >
          <AppButtonContent :loading="loading" label="Entrar al CRM" loading-label="Ingresando…" />
        </button>
      </form>

      <aside class="desktop-login-help border-border bg-primary-soft text-primary" aria-label="Ayuda">
        <ChatBubbleLeftRightIcon class="desktop-help-icon" aria-hidden="true" />
        <div class="desktop-help-copy">
          <strong>¿Necesitás ayuda?</strong>
          <span>Contactá a soporte técnico para recibir asistencia.</span>
        </div>
        <a href="mailto:soporte@ipac.edu.ar">
          <EnvelopeIcon aria-hidden="true" />
          soporte@ipac.edu.ar
        </a>
        <a href="tel:+543743123456">
          <PhoneIcon aria-hidden="true" />
          +54 3743 123456
        </a>
      </aside>
    </section>
  </main>
</template>

<script setup>
import { reactive, ref } from 'vue'
import {
  BuildingOffice2Icon,
  ChatBubbleLeftRightIcon,
  CurrencyDollarIcon,
  EnvelopeIcon,
  EyeIcon,
  EyeSlashIcon,
  LockClosedIcon,
  PhoneIcon,
  UserGroupIcon,
  UserIcon,
  WalletIcon,
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

const features = [
  {
    title: 'Alumnos',
    description: 'Gestioná la información de alumnos, cursos, estados y documentación.',
    icon: UserGroupIcon,
  },
  {
    title: 'Pagos y cobranzas',
    description: 'Controlá pagos, vencimientos y morosidad en tiempo real.',
    icon: CurrencyDollarIcon,
  },
  {
    title: 'Sucursales',
    description: 'Administrá múltiples sucursales y supervisá su desempeño fácilmente.',
    icon: BuildingOffice2Icon,
  },
  {
    title: 'Caja',
    description: 'Controlá el flujo de caja diario sin perder contexto de tus operaciones.',
    icon: WalletIcon,
  },
]

function submitForm() {
  if (props.loading) return
  emit('submit', { ...form })
}
</script>
