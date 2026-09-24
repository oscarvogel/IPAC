<template>
  <form class="notification-settings" @submit.prevent="save">
    <div class="notice">
      <strong>Notificaciones de consultas no resueltas</strong>
      <p>
        Las credenciales SMTP se configuran en el servidor. Acá sólo se define cuándo y a quién avisar.
      </p>
    </div>

    <label class="switch-row">
      <input v-model="form.email_habilitado" type="checkbox" :disabled="!canEdit" />
      <span>
        <strong>Email habilitado</strong>
        <small>Activa los avisos según el modo seleccionado.</small>
      </span>
    </label>

    <label>
      <span>Modo</span>
      <select
        v-model="form.modo_email"
        data-testid="assistant-email-mode"
        :disabled="!canEdit"
      >
        <option value="desactivado">Desactivado</option>
        <option value="inmediato">Inmediato</option>
        <option value="diario">Resumen diario</option>
      </select>
    </label>

    <label>
      <span>Destinatarios</span>
      <textarea
        v-model="recipientText"
        rows="4"
        :disabled="!canEdit"
        placeholder="uno@ipac.com.ar&#10;otro@ipac.com.ar"
      />
      <small>Un email por línea o separados por coma.</small>
    </label>

    <label v-if="form.modo_email === 'diario'">
      <span>Hora del resumen</span>
      <input v-model="form.hora_resumen_diario" type="time" :disabled="!canEdit" />
    </label>

    <label class="switch-row">
      <input v-model="form.incluir_fuera_de_alcance" type="checkbox" :disabled="!canEdit" />
      <span>
        <strong>Incluir preguntas fuera de IPAC</strong>
        <small>Por defecto se auditan, pero no generan correo.</small>
      </span>
    </label>

    <p v-if="!canEdit" class="read-only">
      Sólo Superadmin puede cambiar la configuración de correo.
    </p>

    <button v-if="canEdit" class="btn-primary" type="submit">Guardar notificaciones</button>
  </form>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
  canEdit: { type: Boolean, default: false },
})
const emit = defineEmits(['save'])

const form = reactive({})
const recipientText = ref('')

watch(
  () => props.modelValue,
  (value) => {
    Object.assign(form, {
      email_habilitado: value?.email_habilitado ?? false,
      modo_email: value?.modo_email || 'desactivado',
      incluir_fuera_de_alcance: value?.incluir_fuera_de_alcance ?? false,
      hora_resumen_diario: (value?.hora_resumen_diario || '18:00').slice(0, 5),
    })
    recipientText.value = (value?.destinatarios || []).join('\n')
  },
  { immediate: true, deep: true },
)

function save() {
  const destinatarios = recipientText.value
    .split(/[\n,;]+/)
    .map((value) => value.trim())
    .filter(Boolean)
  emit('save', {
    email_habilitado: form.email_habilitado,
    modo_email: form.modo_email,
    destinatarios,
    incluir_fuera_de_alcance: form.incluir_fuera_de_alcance,
    hora_resumen_diario: form.hora_resumen_diario,
  })
}
</script>

<style scoped>
.notification-settings { display: grid; gap: 1rem; max-width: 46rem; }
.notification-settings label { display: grid; gap: .35rem; }
.notification-settings input, .notification-settings select, .notification-settings textarea { border: 1px solid var(--color-border); border-radius: .7rem; padding: .65rem .75rem; background: var(--color-surface); color: var(--color-text-primary); }
.notification-settings small, .notice p, .read-only { color: var(--color-text-secondary); }
.notice { border: 1px solid var(--color-border); border-radius: .9rem; padding: .9rem; background: var(--primary-soft); }
.notice p { margin: .3rem 0 0; }
.switch-row { grid-template-columns: auto 1fr; align-items: start; }
.switch-row input { margin-top: .2rem; }
.switch-row span { display: grid; gap: .2rem; }
.btn-primary { width: fit-content; border: 0; border-radius: .65rem; padding: .6rem .9rem; background: var(--primary); color: white; font-weight: 700; cursor: pointer; }
</style>
