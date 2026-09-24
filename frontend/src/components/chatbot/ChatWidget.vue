<template>
  <button
    v-if="!isOpen"
    class="ipac-chat-fab"
    type="button"
    aria-label="Abrir Asistente IPAC"
    title="Abrir Asistente IPAC"
    @click="openChat"
  >
    <SparklesIcon aria-hidden="true" />
  </button>

  <section
    v-else
    class="ipac-chat-panel"
    :class="{ 'ipac-chat-panel--maximized': isMaximized }"
    role="dialog"
    aria-modal="true"
    aria-labelledby="ipac-chat-title"
  >
    <header class="ipac-chat-header">
      <div class="ipac-chat-heading">
        <span class="ipac-chat-icon"><SparklesIcon aria-hidden="true" /></span>
        <span>
          <strong id="ipac-chat-title">Asistente IPAC</strong>
          <small>Ayuda operativa del sistema</small>
        </span>
      </div>
      <div class="ipac-chat-header-actions">
        <button
          type="button"
          aria-label="Nueva conversación"
          title="Nueva conversación"
          @click="newConversation"
        >
          <ArrowPathIcon aria-hidden="true" />
        </button>
        <button
          type="button"
          :aria-label="isMaximized ? 'Restaurar asistente' : 'Maximizar asistente'"
          :title="isMaximized ? 'Restaurar' : 'Maximizar'"
          @click="isMaximized = !isMaximized"
        >
          <ArrowsPointingInIcon v-if="isMaximized" aria-hidden="true" />
          <ArrowsPointingOutIcon v-else aria-hidden="true" />
        </button>
        <button type="button" aria-label="Cerrar asistente" title="Cerrar" @click="isOpen = false">
          <XMarkIcon aria-hidden="true" />
        </button>
      </div>
    </header>

    <div ref="messagesContainer" class="ipac-chat-messages" role="log" aria-live="polite">
      <div
        v-for="message in messages"
        :key="message.localId || message.id"
        class="ipac-chat-message"
        :class="'ipac-chat-message--' + message.role"
      >
        <span class="ipac-chat-message-role">{{ message.role === 'user' ? 'Vos' : 'IPAC' }}</span>
        <p>{{ message.content }}</p>
        <button
          v-if="message.action"
          class="ipac-chat-action"
          type="button"
          @click="openAction(message.action.path)"
        >
          {{ message.action.label }}
          <ArrowRightIcon aria-hidden="true" />
        </button>
      </div>

      <div v-if="loading" class="ipac-chat-thinking" role="status">
        <span />
        <span />
        <span />
        Pensando…
      </div>
    </div>

    <div v-if="error" class="ipac-chat-error" role="alert">
      <span>{{ error }}</span>
      <button type="button" @click="error = ''">Cerrar</button>
    </div>

    <div
      v-if="suggestions.length && !loading"
      class="ipac-chat-suggestions"
      data-testid="chat-quick-actions"
      aria-label="Consultas rápidas"
    >
      <button
        v-for="suggestion in suggestions"
        :key="suggestion"
        type="button"
        @click="sendSuggestion(suggestion)"
      >
        {{ suggestion }}
      </button>
    </div>

    <form class="ipac-chat-compose" @submit.prevent="sendMessage">
      <label class="sr-only" for="ipac-chat-input">Mensaje para el Asistente IPAC</label>
      <input
        id="ipac-chat-input"
        v-model="input"
        type="text"
        maxlength="4000"
        autocomplete="off"
        placeholder="Ej: ¿Cómo cierro la caja?"
        :disabled="loading"
      />
      <button type="submit" :disabled="loading || !input.trim()" aria-label="Enviar mensaje" title="Enviar">
        <PaperAirplaneIcon aria-hidden="true" />
      </button>
    </form>
  </section>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowPathIcon,
  ArrowRightIcon,
  ArrowsPointingInIcon,
  ArrowsPointingOutIcon,
  PaperAirplaneIcon,
  SparklesIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { apiRequest } from '@/lib/api'

const STORAGE_KEY = 'ipac.chatbot.conversation.native-tools-v1'
const LEGACY_STORAGE_KEYS = ['ipac.chatbot.conversation']
const router = useRouter()
const isOpen = ref(false)
const isMaximized = ref(false)
const loading = ref(false)
const input = ref('')
const error = ref('')
const conversationId = ref(null)
const messages = ref([])
const suggestions = ref([
  '¿Cómo doy de alta un alumno?',
  '¿Cómo genero cuotas?',
  '¿Cómo registro un pago?',
  '¿Cómo cierro la caja?',
])
const messagesContainer = ref(null)
let localId = 0
let initialized = false

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

async function loadSuggestions() {
  try {
    const data = await apiRequest('/chatbot/briefing/')
    if (Array.isArray(data?.suggestions) && data.suggestions.length) {
      suggestions.value = data.suggestions
    }
  } catch {
    // Las acciones rápidas locales permiten seguir usando el asistente.
  }
}

function clearLegacyConversationKeys() {
  try {
    for (const key of LEGACY_STORAGE_KEYS) {
      window.localStorage.removeItem(key)
    }
  } catch {
    // El chat puede seguir funcionando sin localStorage.
  }
}

async function openChat() {
  isOpen.value = true
  if (!initialized) {
    initialized = true
    clearLegacyConversationKeys()
    await restoreOrStartConversation()
    loadSuggestions()
  }
  scrollToBottom()
}

async function restoreOrStartConversation() {
  let stored = null
  try {
    stored = window.localStorage.getItem(STORAGE_KEY)
  } catch {
    stored = null
  }

  if (stored) {
    try {
      const data = await apiRequest('/chatbot/history/', {
        query: { conversation_id: stored },
      })
      conversationId.value = data.conversation.id
      messages.value = (data.messages || []).map((message) => ({
        ...message,
        localId: ++localId,
      }))
      scrollToBottom()
      return
    } catch {
      try {
        window.localStorage.removeItem(STORAGE_KEY)
      } catch {
        // no-op
      }
    }
  }

  await startConversation()
}

async function startConversation() {
  loading.value = true
  error.value = ''
  try {
    const data = await apiRequest('/chatbot/conversations/', {
      method: 'POST',
      body: {},
    })
    conversationId.value = data.conversation.id
    messages.value = (data.messages || []).map((message) => ({
      ...message,
      localId: ++localId,
    }))
    try {
      window.localStorage.setItem(STORAGE_KEY, String(conversationId.value))
    } catch {
      // El chat sigue funcionando aunque localStorage no esté disponible.
    }
  } catch (err) {
    error.value = err.message || 'No se pudo iniciar el Asistente IPAC.'
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

async function newConversation() {
  if (loading.value) return
  try {
    window.localStorage.removeItem(STORAGE_KEY)
  } catch {
    // no-op
  }
  conversationId.value = null
  messages.value = []
  input.value = ''
  error.value = ''
  await startConversation()
}

async function sendMessage() {
  const content = input.value.trim()
  if (!content || loading.value) return

  if (!conversationId.value) {
    await startConversation()
    if (!conversationId.value) return
  }

  messages.value.push({
    localId: ++localId,
    role: 'user',
    content,
  })
  input.value = ''
  loading.value = true
  error.value = ''
  scrollToBottom()

  try {
    const data = await apiRequest('/chatbot/messages/', {
      method: 'POST',
      body: {
        conversation_id: conversationId.value,
        content,
      },
    })
    const assistant = (data.messages || []).find((message) => message.role === 'assistant')
    if (assistant) {
      messages.value.push({
        ...assistant,
        localId: ++localId,
        action: data.action || null,
      })
    }
  } catch (err) {
    error.value = err.message || 'No se pudo consultar el Asistente IPAC.'
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function sendSuggestion(suggestion) {
  input.value = suggestion
  sendMessage()
}

function openAction(path) {
  if (!path) return
  isOpen.value = false
  router.push(path)
}
</script>

<style scoped>
.ipac-chat-fab {
  position: fixed;
  right: 1.5rem;
  bottom: 1.5rem;
  z-index: 70;
  display: grid;
  width: 3.6rem;
  height: 3.6rem;
  place-items: center;
  border: 0;
  border-radius: 999px;
  background: var(--primary);
  color: var(--primary-foreground, #fff);
  box-shadow: 0 18px 40px rgb(15 23 42 / 24%);
  cursor: pointer;
  transition: transform .18s ease, background .18s ease;
}

.ipac-chat-fab:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
}

.ipac-chat-fab svg {
  width: 1.55rem;
  height: 1.55rem;
}

.ipac-chat-panel {
  position: fixed;
  right: 1.5rem;
  bottom: 1.5rem;
  z-index: 80;
  display: flex;
  width: min(25rem, calc(100vw - 2rem));
  height: min(38rem, calc(100dvh - 2rem));
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 1.15rem;
  background: var(--surface);
  color: var(--text-primary);
  box-shadow: 0 24px 70px rgb(15 23 42 / 28%);
}

.ipac-chat-panel--maximized {
  inset: 1rem;
  width: auto;
  height: auto;
}

.ipac-chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .75rem;
  padding: .9rem 1rem;
  background: var(--primary);
  color: var(--primary-foreground, #fff);
}

.ipac-chat-heading {
  display: flex;
  align-items: center;
  gap: .65rem;
}

.ipac-chat-header strong,
.ipac-chat-header small {
  display: block;
}

.ipac-chat-header small {
  margin-top: .1rem;
  opacity: .78;
  font-size: .72rem;
}

.ipac-chat-icon {
  display: grid;
  width: 2rem;
  height: 2rem;
  place-items: center;
  border-radius: .7rem;
  background: rgb(255 255 255 / 13%);
}

.ipac-chat-icon svg,
.ipac-chat-header-actions svg,
.ipac-chat-compose svg,
.ipac-chat-action svg {
  width: 1.1rem;
  height: 1.1rem;
}

.ipac-chat-header-actions {
  display: flex;
  gap: .25rem;
}

.ipac-chat-header-actions button {
  display: grid;
  width: 2.25rem;
  height: 2.25rem;
  place-items: center;
  border: 0;
  border-radius: .65rem;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.ipac-chat-header-actions button:hover {
  background: rgb(255 255 255 / 12%);
}

.ipac-chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.ipac-chat-message {
  max-width: 90%;
  margin-bottom: .8rem;
  border: 1px solid var(--border);
  border-radius: .9rem;
  padding: .7rem .8rem;
  background: var(--surface-raised, var(--surface));
}

.ipac-chat-message--user {
  margin-left: auto;
  border-color: color-mix(in srgb, var(--primary) 28%, var(--border));
  background: color-mix(in srgb, var(--primary) 8%, var(--surface));
}

.ipac-chat-message-role {
  display: block;
  margin-bottom: .25rem;
  color: var(--text-secondary);
  font-size: .68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .06em;
}

.ipac-chat-message p {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.45;
  font-size: .88rem;
}

.ipac-chat-action {
  display: inline-flex;
  align-items: center;
  gap: .35rem;
  margin-top: .65rem;
  border: 0;
  border-radius: .65rem;
  padding: .5rem .65rem;
  background: var(--primary);
  color: var(--primary-foreground, #fff);
  font-weight: 700;
  cursor: pointer;
}

.ipac-chat-thinking {
  display: flex;
  align-items: center;
  gap: .28rem;
  color: var(--text-secondary);
  font-size: .8rem;
}

.ipac-chat-thinking span {
  width: .35rem;
  height: .35rem;
  border-radius: 999px;
  background: currentColor;
  animation: ipac-chat-pulse 1s infinite alternate;
}

.ipac-chat-thinking span:nth-child(2) { animation-delay: .15s; }
.ipac-chat-thinking span:nth-child(3) { animation-delay: .3s; }

@keyframes ipac-chat-pulse {
  to { opacity: .25; transform: translateY(-2px); }
}

.ipac-chat-error {
  display: flex;
  justify-content: space-between;
  gap: .5rem;
  border-top: 1px solid var(--border);
  padding: .55rem .75rem;
  background: var(--danger-soft, #fff1f2);
  color: var(--danger, #b91c1c);
  font-size: .78rem;
}

.ipac-chat-error button {
  border: 0;
  background: transparent;
  color: inherit;
  text-decoration: underline;
  cursor: pointer;
}

.ipac-chat-suggestions {
  display: flex;
  gap: .4rem;
  overflow-x: auto;
  border-top: 1px solid var(--border);
  padding: .6rem .75rem;
}

.ipac-chat-suggestions button {
  flex: 0 0 auto;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: .4rem .65rem;
  background: var(--surface);
  color: var(--text-primary);
  font-size: .72rem;
  cursor: pointer;
}

.ipac-chat-suggestions button:hover {
  border-color: var(--primary);
}

.ipac-chat-compose {
  display: flex;
  gap: .5rem;
  border-top: 1px solid var(--border);
  padding: .75rem;
}

.ipac-chat-compose input {
  min-width: 0;
  flex: 1;
  border: 1px solid var(--border);
  border-radius: .75rem;
  padding: .68rem .78rem;
  background: var(--surface);
  color: var(--text-primary);
}

.ipac-chat-compose input:focus {
  outline: 2px solid color-mix(in srgb, var(--primary) 35%, transparent);
  border-color: var(--primary);
}

.ipac-chat-compose button {
  display: grid;
  width: 2.65rem;
  place-items: center;
  border: 0;
  border-radius: .75rem;
  background: var(--primary);
  color: var(--primary-foreground, #fff);
  cursor: pointer;
}

.ipac-chat-compose button:disabled {
  cursor: not-allowed;
  opacity: .45;
}

@media (max-width: 640px) {
  .ipac-chat-fab {
    right: 1rem;
    bottom: 1rem;
  }

  .ipac-chat-panel {
    inset: .65rem;
    width: auto;
    height: auto;
    border-radius: 1rem;
  }

  .ipac-chat-panel--maximized {
    inset: .35rem;
  }
}
</style>
