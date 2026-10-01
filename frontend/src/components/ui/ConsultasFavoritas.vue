<template>
  <section class="favorites" aria-label="Consultas favoritas">
    <div class="favorites-controls">
      <label>Consultas favoritas
        <select v-model="selected" :disabled="busy || loading">
          <option value="">Elegir una consulta guardada</option>
          <option v-for="item in favoritas" :key="item.id" :value="item.id">{{ item.nombre }}</option>
        </select>
      </label>
      <button type="button" :disabled="!selected || busy || disabled" @click="apply">Aplicar favorita</button>
      <button type="button" :disabled="busy || disabled" @click="editing = 'crear'; name = ''">Guardar consulta actual</button>
      <button v-if="selected" type="button" :disabled="busy" @click="editing = 'renombrar'; name = selectedItem?.nombre || ''">Renombrar</button>
      <button v-if="selected" type="button" :disabled="busy || disabled" @click="editing = 'actualizar'">Actualizar con filtros actuales</button>
      <button v-if="selected" type="button" :disabled="busy" @click="editing = 'eliminar'">Eliminar</button>
    </div>
    <form v-if="editing" class="favorites-edit" @submit.prevent="save">
      <label v-if="editing === 'crear' || editing === 'renombrar'">Nombre de la consulta<input v-model="name" maxlength="80" required :disabled="busy" /></label>
      <p v-else>{{ editing === 'eliminar' ? '¿Eliminar esta consulta favorita?' : '¿Reemplazar esta favorita por los filtros actuales?' }}</p>
      <button type="submit" :disabled="busy || (editing === 'actualizar' && disabled)">{{ busy ? 'Guardando…' : 'Confirmar' }}</button>
      <button type="button" :disabled="busy" @click="editing = ''">Cancelar</button>
    </form>
    <p v-if="message" role="status">{{ message }}</p>
    <p v-if="actionError || error" role="alert">{{ actionError || error }} <button v-if="error" type="button" @click="load">Reintentar carga</button></p>
    <small>Guardadas en tu cuenta. Aplicarlas conserva los permisos de tu perfil.</small>
  </section>
</template>
<script setup>
import { computed, ref, watch } from 'vue'
import { useConsultasFavoritas } from '@/composables/useConsultasFavoritas'
import { useAuth } from '@/composables/useAuth'
const props = defineProps({ pantalla: { type: String, required: true }, configuracion: { type: Object, required: true }, disabled: Boolean })
const emit = defineEmits(['aplicar'])
const { favoritas, loading, error, load, crear, actualizar, eliminar, obtener } = useConsultasFavoritas(props.pantalla)
const auth = useAuth()
let actionRevision = 0
const selected = ref(''), editing = ref(''), name = ref(''), busy = ref(false), actionError = ref(''), message = ref('')
const selectedItem = computed(() => favoritas.value.find(item => item.id === selected.value))
watch(() => auth.user.value?.id, () => { actionRevision++; selected.value = ''; editing.value = ''; actionError.value = ''; message.value = ''; busy.value = false }, { flush: 'sync' })
async function run(action) {
  if (busy.value) return
  busy.value = true; actionError.value = ''; message.value = ''
  const revision = actionRevision
  try { await action() } catch (err) { if (revision === actionRevision) actionError.value = err.message } finally { if (revision === actionRevision) busy.value = false }
}
function apply() { return run(async () => { const item = await obtener(selected.value); emit('aplicar', item.configuracion) }) }
function save() {
  return run(async () => {
    if (editing.value === 'crear') { const item = await crear(name.value, props.configuracion); selected.value = item.id }
    if (editing.value === 'renombrar') await actualizar(selected.value, { nombre: name.value })
    if (editing.value === 'actualizar') await actualizar(selected.value, { configuracion: props.configuracion })
    if (editing.value === 'eliminar') { await eliminar(selected.value); selected.value = '' }
    editing.value = ''; message.value = 'Consulta favorita guardada.'
  })
}
</script>
<style scoped>
.favorites{display:grid;gap:.65rem;padding:1rem;border:1px solid var(--border);border-radius:.8rem;background:var(--surface);color:var(--text-primary)}.favorites-controls,.favorites-edit{display:flex;flex-wrap:wrap;align-items:end;gap:.55rem}.favorites label{display:grid;gap:.3rem;font-size:.85rem;font-weight:700;min-width:0}.favorites select,.favorites input{width:100%;min-height:44px;max-width:100%;padding:.55rem;border:1px solid var(--border);border-radius:.5rem;background:var(--surface);color:var(--text-primary)}.favorites button{min-height:44px;padding:.5rem .75rem;border:1px solid var(--border);border-radius:.5rem;background:var(--surface-soft);color:var(--primary);font-weight:700;white-space:normal}.favorites button:disabled{opacity:.5}.favorites small,.favorites p{margin:0;color:var(--text-secondary)}.favorites [role=alert]{color:var(--danger)}.favorites :focus-visible{outline:3px solid var(--primary);outline-offset:2px}@media(max-width:560px){.favorites-controls>label,.favorites-edit>label{width:100%}.favorites-controls>button{flex:1 1 auto}}
</style>
