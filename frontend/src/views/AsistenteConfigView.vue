<template>
  <section class="assistant-admin">
    <header class="page-head">
      <div>
        <p class="eyebrow">Configuración</p>
        <h1>Asistente IA</h1>
        <p>Conocimiento, consultas pendientes y avisos del Asistente IPAC.</p>
      </div>
      <button
        v-if="activeTab === 'knowledge' && !editorOpen"
        type="button"
        class="btn-primary"
        @click="openNewArticle"
      >
        Nuevo artículo
      </button>
    </header>

    <nav class="tabs" aria-label="Secciones del Asistente IA">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
        <span v-if="tab.id === 'unresolved' && pendingCount">{{ pendingCount }}</span>
      </button>
    </nav>

    <div v-if="error" class="message error" role="alert">{{ error }}</div>
    <div v-if="notice" class="message success" role="status">{{ notice }}</div>

    <KnowledgeEditor
      v-if="activeTab === 'knowledge' && editorOpen"
      :model-value="editingArticle"
      @save="saveArticle"
      @cancel="closeEditor"
    />

    <template v-else-if="activeTab === 'knowledge'">
      <div class="filters">
        <input v-model.trim="knowledgeFilters.search" placeholder="Buscar título o clave…" @input="debouncedKnowledge" />
        <select v-model="knowledgeFilters.modulo" @change="loadKnowledge">
          <option value="">Todos los módulos</option>
          <option v-for="module in modules" :key="module" :value="module">{{ module }}</option>
        </select>
        <select v-model="knowledgeFilters.activo" @change="loadKnowledge">
          <option value="">Todos</option>
          <option value="true">Activos</option>
          <option value="false">Inactivos</option>
        </select>
      </div>

      <div v-if="loading" class="empty">Cargando conocimiento…</div>
      <div v-else-if="!knowledge.length" class="empty">No hay artículos para estos filtros.</div>
      <div v-else class="knowledge-grid">
        <article v-for="article in knowledge" :key="article.id" class="knowledge-card">
          <header>
            <div>
              <span class="badge">{{ article.modulo }}</span>
              <h3>{{ article.titulo }}</h3>
            </div>
            <span :class="['state', { off: !article.activo }]">{{ article.activo ? 'Activo' : 'Inactivo' }}</span>
          </header>
          <p>{{ article.descripcion || ((article.pasos?.length || 0) + ' paso(s) configurados.') }}</p>
          <small>{{ article.preguntas_equivalentes?.length || 0 }} pregunta(s) equivalente(s)</small>
          <footer>
            <button type="button" class="btn-secondary" @click="editArticle(article)">Editar</button>
            <button type="button" class="btn-secondary" @click="toggleArticle(article)">
              {{ article.activo ? 'Desactivar' : 'Activar' }}
            </button>
          </footer>
        </article>
      </div>
    </template>

    <template v-else-if="activeTab === 'unresolved'">
      <div class="filters">
        <input v-model.trim="unresolvedFilters.search" placeholder="Buscar pregunta…" @input="debouncedUnresolved" />
        <select v-model="unresolvedFilters.estado" @change="loadUnresolved">
          <option value="">Todos los estados</option>
          <option value="pendiente">Pendientes</option>
          <option value="resuelta">Resueltas</option>
          <option value="ignorada">Ignoradas</option>
        </select>
        <select v-model="unresolvedFilters.categoria" @change="loadUnresolved">
          <option value="">Todas las categorías</option>
          <option value="no_documentada">No documentada</option>
          <option value="sin_datos">Sin datos</option>
          <option value="sin_permiso">Sin permiso</option>
          <option value="fuera_de_alcance">Fuera de alcance</option>
          <option value="error_ia">Error IA</option>
          <option value="error_herramienta">Error herramienta</option>
        </select>
      </div>
      <UnresolvedList
        :items="unresolved"
        :loading="loading"
        @create-article="openArticleFromUnresolved"
        @resolve="resolveUnresolved"
        @ignore="ignoreUnresolved"
      />
    </template>

    <NotificationSettings
      v-else
      :model-value="config"
      :can-edit="canConfigureNotifications"
      @save="saveConfig"
    />
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import KnowledgeEditor from '@/components/asistente/KnowledgeEditor.vue'
import NotificationSettings from '@/components/asistente/NotificationSettings.vue'
import UnresolvedList from '@/components/asistente/UnresolvedList.vue'
import { useAssistantAdmin } from '@/composables/useAssistantAdmin'
import { useAuth } from '@/composables/useAuth'

const api = useAssistantAdmin()
const auth = useAuth()

const tabs = [
  { id: 'knowledge', label: 'Base de conocimiento' },
  { id: 'unresolved', label: 'Consultas no resueltas' },
  { id: 'notifications', label: 'Notificaciones' },
]
const modules = ['alumnos', 'cobranzas', 'cuotas', 'caja', 'reportes', 'configuracion', 'importacion', 'otro']

const activeTab = ref('knowledge')
const loading = ref(false)
const error = ref('')
const notice = ref('')
const knowledge = ref([])
const unresolved = ref([])
const config = ref({})
const editorOpen = ref(false)
const editingArticle = ref({})
const sourceEventId = ref(null)
const pendingCount = computed(() => unresolved.value.filter((item) => item.estado === 'pendiente').length)
const canConfigureNotifications = computed(() => auth.can('configure-assistant-notifications'))

const knowledgeFilters = reactive({ search: '', modulo: '', activo: '' })
const unresolvedFilters = reactive({ search: '', estado: 'pendiente', categoria: '' })

let knowledgeTimer = null
let unresolvedTimer = null

function rows(data) {
  return Array.isArray(data) ? data : (data?.results || [])
}

function showNotice(message) {
  notice.value = message
  window.setTimeout(() => {
    if (notice.value === message) notice.value = ''
  }, 3500)
}

async function loadKnowledge() {
  loading.value = true
  error.value = ''
  try {
    knowledge.value = rows(await api.listKnowledge(knowledgeFilters))
  } catch (err) {
    error.value = err.message || 'No se pudo cargar la base de conocimiento.'
  } finally {
    loading.value = false
  }
}

async function loadUnresolved() {
  loading.value = true
  error.value = ''
  try {
    unresolved.value = rows(await api.listUnresolved(unresolvedFilters))
  } catch (err) {
    error.value = err.message || 'No se pudieron cargar las consultas no resueltas.'
  } finally {
    loading.value = false
  }
}

async function loadConfig() {
  loading.value = true
  error.value = ''
  try {
    config.value = await api.getConfig()
  } catch (err) {
    error.value = err.message || 'No se pudo cargar la configuración del asistente.'
  } finally {
    loading.value = false
  }
}

function debouncedKnowledge() {
  window.clearTimeout(knowledgeTimer)
  knowledgeTimer = window.setTimeout(loadKnowledge, 250)
}

function debouncedUnresolved() {
  window.clearTimeout(unresolvedTimer)
  unresolvedTimer = window.setTimeout(loadUnresolved, 250)
}

function openNewArticle() {
  sourceEventId.value = null
  editingArticle.value = {
    clave: '',
    titulo: '',
    modulo: 'alumnos',
    preguntas_equivalentes: [],
    descripcion: '',
    pasos: [],
    ruta: '',
    action_label: '',
    roles_permitidos: ['superadmin', 'administracion'],
    notas: [],
    activo: true,
    orden: 0,
  }
  editorOpen.value = true
}

function editArticle(article) {
  sourceEventId.value = null
  editingArticle.value = { ...article }
  editorOpen.value = true
}

function closeEditor() {
  editorOpen.value = false
  editingArticle.value = {}
  sourceEventId.value = null
}

async function saveArticle(payload) {
  error.value = ''
  try {
    if (sourceEventId.value) {
      await api.createArticleFromUnresolved(sourceEventId.value, payload)
      showNotice('Artículo creado y consulta marcada como resuelta.')
    } else if (editingArticle.value?.id) {
      await api.updateKnowledge(editingArticle.value.id, payload)
      showNotice('Artículo actualizado.')
    } else {
      await api.createKnowledge(payload)
      showNotice('Artículo creado.')
    }
    closeEditor()
    activeTab.value = 'knowledge'
    await loadKnowledge()
  } catch (err) {
    error.value = err.message || 'No se pudo guardar el artículo.'
  }
}

async function toggleArticle(article) {
  error.value = ''
  try {
    if (article.activo) await api.deactivateKnowledge(article.id)
    else await api.activateKnowledge(article.id)
    await loadKnowledge()
  } catch (err) {
    error.value = err.message || 'No se pudo cambiar el estado del artículo.'
  }
}

function openArticleFromUnresolved(item) {
  sourceEventId.value = item.id
  editingArticle.value = {
    clave: '',
    titulo: '',
    modulo: 'otro',
    preguntas_equivalentes: [item.pregunta],
    descripcion: '',
    pasos: [],
    ruta: '',
    action_label: '',
    roles_permitidos: ['superadmin', 'administracion', 'tesoreria', 'caja', 'consulta'],
    notas: [],
    activo: true,
    orden: 0,
  }
  activeTab.value = 'knowledge'
  editorOpen.value = true
}

async function resolveUnresolved(item) {
  try {
    await api.resolveUnresolved(item.id)
    await loadUnresolved()
  } catch (err) {
    error.value = err.message || 'No se pudo resolver la consulta.'
  }
}

async function ignoreUnresolved(item) {
  try {
    await api.ignoreUnresolved(item.id)
    await loadUnresolved()
  } catch (err) {
    error.value = err.message || 'No se pudo ignorar la consulta.'
  }
}

async function saveConfig(payload) {
  error.value = ''
  try {
    config.value = await api.updateConfig(payload)
    showNotice('Configuración de notificaciones actualizada.')
  } catch (err) {
    error.value = err.message || 'No se pudo guardar la configuración.'
  }
}

watch(activeTab, async (tab) => {
  error.value = ''
  notice.value = ''
  if (tab !== 'knowledge') closeEditor()
  if (tab === 'knowledge') await loadKnowledge()
  else if (tab === 'unresolved') await loadUnresolved()
  else await loadConfig()
})

onMounted(async () => {
  await Promise.all([loadKnowledge(), loadUnresolved(), loadConfig()])
})
</script>

<style scoped>
.assistant-admin { display: grid; gap: 1rem; }
.page-head { display: flex; align-items: end; justify-content: space-between; gap: 1rem; }
.page-head h1 { margin: .15rem 0; }
.page-head p:last-child { margin: 0; color: var(--color-text-secondary); }
.tabs { display: flex; gap: .35rem; overflow-x: auto; border-bottom: 1px solid var(--color-border); }
.tabs button { display: inline-flex; align-items: center; gap: .4rem; border: 0; border-bottom: 2px solid transparent; padding: .75rem .85rem; background: transparent; color: var(--color-text-secondary); font-weight: 700; cursor: pointer; white-space: nowrap; }
.tabs button.active { border-bottom-color: var(--primary); color: var(--primary); }
.tabs span { min-width: 1.4rem; border-radius: 999px; padding: .12rem .35rem; background: var(--primary-soft); font-size: .7rem; }
.filters { display: grid; grid-template-columns: minmax(12rem, 2fr) repeat(2, minmax(10rem, 1fr)); gap: .65rem; }
.filters input, .filters select { min-width: 0; border: 1px solid var(--color-border); border-radius: .7rem; padding: .65rem .75rem; background: var(--color-surface); color: var(--color-text-primary); }
.knowledge-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr)); gap: .8rem; }
.knowledge-card { display: grid; gap: .6rem; border: 1px solid var(--color-border); border-radius: .9rem; padding: .9rem; background: var(--color-surface); }
.knowledge-card header { display: flex; align-items: start; justify-content: space-between; gap: .65rem; }
.knowledge-card h3 { margin: .3rem 0 0; }
.knowledge-card p { margin: 0; color: var(--color-text-secondary); }
.knowledge-card footer { display: flex; gap: .45rem; margin-top: auto; }
.badge, .state { border-radius: 999px; padding: .2rem .48rem; font-size: .7rem; font-weight: 800; }
.badge { background: var(--primary-soft); color: var(--primary); }
.state { background: var(--primary-soft); color: var(--primary); }
.state.off { background: var(--color-surface-muted, #f3f4f6); color: var(--color-text-secondary); }
.message { border-radius: .7rem; padding: .65rem .8rem; }
.message.error { background: var(--danger-soft, #fff1f2); color: var(--danger, #b91c1c); }
.message.success { background: var(--primary-soft); color: var(--primary); }
.btn-primary, .btn-secondary { border-radius: .65rem; padding: .55rem .75rem; cursor: pointer; }
.btn-primary { border: 0; background: var(--primary); color: white; font-weight: 700; }
.btn-secondary { border: 1px solid var(--color-border); background: var(--color-surface); color: var(--color-text-primary); }
.empty { padding: 2rem; text-align: center; color: var(--color-text-secondary); }
@media (max-width: 720px) {
  .page-head { align-items: stretch; flex-direction: column; }
  .filters { grid-template-columns: 1fr; }
}
</style>
