<template>
  <section class="audit-view">
    <header class="audit-header">
      <div>
        <p class="eyebrow">Configuración · Control</p>
        <h1>Auditoría</h1>
        <p>Registro de quién realizó cada cambio sensible y cuándo ocurrió.</p>
      </div>
      <RouterLink to="/configuracion" class="audit-back">Volver a configuración</RouterLink>
    </header>

    <form class="audit-filters" @submit.prevent="load(1)">
      <label>Desde <input v-model="filters.desde" type="date" /></label>
      <label>Hasta <input v-model="filters.hasta" type="date" /></label>
      <label>Módulo
        <select v-model="filters.modulo">
          <option value="">Todos</option>
          <option v-for="module in modules" :key="module" :value="module">{{ module }}</option>
        </select>
      </label>
      <label>Entidad <input v-model.trim="filters.entidad" placeholder="Ej. core.Pago" /></label>
      <button type="submit">Aplicar filtros</button>
    </form>

    <AppPageState v-if="loading || error" :loading="loading" :error="error" label="la auditoría" @retry="load(page)" />
    <div v-else class="audit-table-wrap">
      <table class="audit-table">
        <thead><tr><th>Fecha y hora</th><th>Usuario</th><th>Módulo</th><th>Acción</th><th>Entidad</th><th>Descripción</th></tr></thead>
        <tbody>
          <tr v-for="event in events" :key="event.id">
            <td>{{ formatDateTime(event.creado) }}</td>
            <td>{{ event.usuario_nombre || 'Sistema' }}</td>
            <td><span class="audit-module">{{ event.modulo }}</span></td>
            <td>{{ event.accion }}</td>
            <td>{{ event.entidad }} #{{ event.entidad_id }}</td>
            <td>{{ event.descripcion || changeSummary(event) }}</td>
          </tr>
          <tr v-if="!events.length"><td colspan="6" class="audit-empty">No hay eventos para los filtros elegidos.</td></tr>
        </tbody>
      </table>
    </div>

    <nav class="students-pagination" aria-label="Paginación de auditoría">
      <button :disabled="page <= 1 || loading" @click="load(page - 1)">Anterior</button>
      <span>Página {{ page }} de {{ totalPages }} · {{ count }} eventos</span>
      <button :disabled="page >= totalPages || loading" @click="load(page + 1)">Siguiente</button>
    </nav>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { apiRequest } from '@/lib/api'
import AppPageState from '@/components/ui/AppPageState.vue'

const events = ref([])
const count = ref(0)
const page = ref(1)
const loading = ref(false)
const error = ref('')
const filters = reactive({ desde: '', hasta: '', modulo: '', entidad: '' })
const modules = ['alumnos', 'trayectoria', 'cobranzas', 'caja', 'identidad', 'organizacion']
const totalPages = computed(() => Math.max(1, Math.ceil(count.value / 25)))

async function load(nextPage = 1) {
  loading.value = true
  error.value = ''
  try {
    const data = await apiRequest('/auditoria/', { query: { ...filters, page: nextPage, page_size: 25 } })
    events.value = data.results || []
    count.value = Number(data.count || 0)
    page.value = nextPage
  } catch (err) {
    error.value = err.message || 'No se pudo cargar la auditoría.'
  } finally {
    loading.value = false
  }
}

function formatDateTime(value) {
  return value ? new Intl.DateTimeFormat('es-AR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : '—'
}

function changeSummary(event) {
  const changed = Object.keys(event.valores_nuevos || {})
  return changed.length ? `${changed.length} campos registrados` : 'Operación registrada'
}

onMounted(() => load())
</script>

<style scoped>
.audit-view { display: grid; gap: 1.25rem; }
.audit-header { display: flex; align-items: end; justify-content: space-between; gap: 1rem; }
.audit-header h1 { margin: .15rem 0 .25rem; }
.audit-header p { margin: 0; color: var(--color-text-secondary); }
.audit-back { color: var(--color-primary); font-weight: 700; }
.audit-filters { display: grid; grid-template-columns: repeat(4, minmax(135px, 1fr)) auto; gap: .75rem; align-items: end; padding: 1rem; border: 1px solid var(--color-border); border-radius: 1rem; background: var(--color-surface); }
.audit-filters label { display: grid; gap: .35rem; color: var(--color-text-secondary); font-size: .78rem; font-weight: 700; }
.audit-filters input, .audit-filters select { min-height: 2.65rem; border: 1px solid var(--color-border); border-radius: .65rem; padding: .55rem .7rem; background: var(--color-surface); color: var(--color-text-primary); }
.audit-filters button { min-height: 2.65rem; border: 0; border-radius: .65rem; padding: 0 1rem; background: var(--color-primary); color: white; font-weight: 800; }
.audit-table-wrap { overflow-x: auto; border: 1px solid var(--color-border); border-radius: 1rem; background: var(--color-surface); }
.audit-table { width: 100%; border-collapse: collapse; min-width: 850px; }
.audit-table th, .audit-table td { padding: .8rem 1rem; border-bottom: 1px solid var(--color-border); text-align: left; vertical-align: top; }
.audit-table th { color: var(--color-text-secondary); font-size: .72rem; text-transform: uppercase; letter-spacing: .04em; }
.audit-module { border-radius: 999px; padding: .22rem .5rem; background: #eaf2ff; color: var(--color-primary); font-size: .75rem; font-weight: 800; }
.audit-empty { padding: 2rem !important; text-align: center !important; color: var(--color-text-secondary); }
@media (max-width: 800px) { .audit-header { align-items: start; flex-direction: column; } .audit-filters { grid-template-columns: 1fr 1fr; } .audit-filters button { grid-column: 1 / -1; } }
@media (max-width: 480px) { .audit-filters { grid-template-columns: 1fr; } .audit-filters button { grid-column: auto; } }
</style>
