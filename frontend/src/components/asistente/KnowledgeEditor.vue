<template>
  <form class="knowledge-editor" @submit.prevent="submit">
    <header class="editor-head">
      <div>
        <p class="eyebrow">{{ form.id ? 'Editar artículo' : 'Nuevo artículo' }}</p>
        <h2>{{ form.titulo || 'Conocimiento del asistente' }}</h2>
      </div>
      <button type="button" class="btn-secondary" @click="$emit('cancel')">Cancelar</button>
    </header>

    <div class="form-grid">
      <label>
        <span>Clave</span>
        <input v-model.trim="form.clave" required maxlength="120" placeholder="ej: refinanciar_cuotas" />
      </label>
      <label>
        <span>Módulo</span>
        <select v-model="form.modulo" required>
          <option v-for="module in modules" :key="module" :value="module">{{ module }}</option>
        </select>
      </label>
      <label class="span-2">
        <span>Título</span>
        <input v-model.trim="form.titulo" required maxlength="180" />
      </label>
      <label class="span-2">
        <span>Descripción</span>
        <textarea v-model.trim="form.descripcion" rows="2" placeholder="Qué resuelve este artículo" />
      </label>
      <label>
        <span>Ruta interna</span>
        <input v-model.trim="form.ruta" placeholder="/alumnos" />
      </label>
      <label>
        <span>Texto del botón</span>
        <input v-model.trim="form.action_label" placeholder="Abrir Alumnos" />
      </label>
    </div>

    <section class="array-section">
      <div class="section-title">
        <div>
          <strong>Preguntas equivalentes</strong>
          <small>Formas en que un operador podría preguntar lo mismo.</small>
        </div>
        <button data-testid="add-alias" type="button" class="btn-secondary" @click="addAlias">Agregar</button>
      </div>
      <div v-for="(_, index) in form.preguntas_equivalentes" :key="`alias-${index}`" class="array-row">
        <input v-model.trim="form.preguntas_equivalentes[index]" data-testid="alias-input" />
        <button type="button" class="icon-danger" title="Quitar" @click="form.preguntas_equivalentes.splice(index, 1)">×</button>
      </div>
    </section>

    <section class="array-section">
      <div class="section-title">
        <div>
          <strong>Pasos</strong>
          <small>Orden exacto que debe explicar el bot.</small>
        </div>
        <button type="button" class="btn-secondary" @click="form.pasos.push('')">Agregar paso</button>
      </div>
      <div v-for="(_, index) in form.pasos" :key="`step-${index}`" class="array-row numbered">
        <span>{{ index + 1 }}</span>
        <input v-model.trim="form.pasos[index]" />
        <button type="button" class="icon-danger" title="Quitar" @click="form.pasos.splice(index, 1)">×</button>
      </div>
    </section>

    <section class="array-section">
      <div class="section-title">
        <div>
          <strong>Notas</strong>
          <small>Advertencias o aclaraciones importantes.</small>
        </div>
        <button type="button" class="btn-secondary" @click="form.notas.push('')">Agregar nota</button>
      </div>
      <div v-for="(_, index) in form.notas" :key="`note-${index}`" class="array-row">
        <input v-model.trim="form.notas[index]" />
        <button type="button" class="icon-danger" title="Quitar" @click="form.notas.splice(index, 1)">×</button>
      </div>
    </section>

    <section class="roles-section">
      <strong>Roles para los que aplica esta ayuda</strong>
      <div class="role-grid">
        <label v-for="role in roles" :key="role.value" class="check-row">
          <input
            type="checkbox"
            :value="role.value"
            :checked="form.roles_permitidos.includes(role.value)"
            @change="toggleRole(role.value)"
          />
          <span>{{ role.label }}</span>
        </label>
      </div>
      <small>Esto controla qué artículo ve cada rol; no concede permisos operativos.</small>
    </section>

    <footer class="editor-footer">
      <label class="check-row">
        <input v-model="form.activo" type="checkbox" />
        <span>Artículo activo</span>
      </label>
      <label class="order-field">
        <span>Orden</span>
        <input v-model.number="form.orden" type="number" />
      </label>
      <button class="btn-primary" type="submit">Guardar artículo</button>
    </footer>
  </form>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Object, required: true },
})
const emit = defineEmits(['save', 'cancel'])

const modules = ['alumnos', 'cobranzas', 'cuotas', 'caja', 'reportes', 'configuracion', 'importacion', 'otro']
const roles = [
  { value: 'superadmin', label: 'Superadmin' },
  { value: 'administracion', label: 'Administración' },
  { value: 'tesoreria', label: 'Tesorería' },
  { value: 'caja', label: 'Caja' },
  { value: 'consulta', label: 'Consulta' },
]

const form = reactive({})

function reset(value) {
  Object.keys(form).forEach((key) => delete form[key])
  Object.assign(form, {
    id: value?.id || null,
    clave: value?.clave || '',
    titulo: value?.titulo || '',
    modulo: value?.modulo || 'alumnos',
    preguntas_equivalentes: [...(value?.preguntas_equivalentes || [])],
    descripcion: value?.descripcion || '',
    pasos: [...(value?.pasos || [])],
    ruta: value?.ruta || '',
    action_label: value?.action_label || '',
    roles_permitidos: [...(value?.roles_permitidos || [])],
    notas: [...(value?.notas || [])],
    activo: value?.activo ?? true,
    orden: value?.orden ?? 0,
  })
}

watch(() => props.modelValue, reset, { immediate: true, deep: true })

function addAlias() {
  form.preguntas_equivalentes.push('')
}

function toggleRole(role) {
  const index = form.roles_permitidos.indexOf(role)
  if (index >= 0) form.roles_permitidos.splice(index, 1)
  else form.roles_permitidos.push(role)
}

function clean(values) {
  return values.map((value) => value.trim()).filter(Boolean)
}

function submit() {
  emit('save', {
    clave: form.clave,
    titulo: form.titulo,
    modulo: form.modulo,
    preguntas_equivalentes: clean(form.preguntas_equivalentes),
    descripcion: form.descripcion,
    pasos: clean(form.pasos),
    ruta: form.ruta,
    action_label: form.action_label,
    roles_permitidos: [...form.roles_permitidos],
    notas: clean(form.notas),
    activo: form.activo,
    orden: Number(form.orden) || 0,
  })
}
</script>

<style scoped>
.knowledge-editor { display: grid; gap: 1rem; }
.editor-head, .section-title, .editor-footer { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.editor-head h2 { margin: .2rem 0 0; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .85rem; }
.form-grid label, .order-field { display: grid; gap: .35rem; }
.span-2 { grid-column: 1 / -1; }
input, select, textarea { width: 100%; border: 1px solid var(--color-border); border-radius: .7rem; padding: .65rem .75rem; background: var(--color-surface); color: var(--color-text-primary); }
.array-section, .roles-section { display: grid; gap: .65rem; border: 1px solid var(--color-border); border-radius: .9rem; padding: .9rem; }
.section-title small, .roles-section small { display: block; color: var(--color-text-secondary); margin-top: .2rem; }
.array-row { display: grid; grid-template-columns: 1fr auto; gap: .45rem; align-items: center; }
.array-row.numbered { grid-template-columns: 1.5rem 1fr auto; }
.role-grid { display: flex; flex-wrap: wrap; gap: .75rem 1.25rem; }
.check-row { display: inline-flex; align-items: center; gap: .45rem; }
.check-row input { width: auto; }
.order-field { width: 7rem; }
.btn-primary, .btn-secondary, .icon-danger { border-radius: .65rem; padding: .55rem .75rem; cursor: pointer; }
.btn-primary { border: 0; background: var(--primary); color: white; font-weight: 700; }
.btn-secondary { border: 1px solid var(--color-border); background: var(--color-surface); color: var(--color-text-primary); }
.icon-danger { border: 0; background: transparent; color: var(--danger, #b91c1c); font-size: 1.25rem; }
@media (max-width: 700px) {
  .form-grid { grid-template-columns: 1fr; }
  .span-2 { grid-column: auto; }
  .editor-head, .editor-footer { align-items: stretch; flex-direction: column; }
  .order-field { width: 100%; }
}
</style>
