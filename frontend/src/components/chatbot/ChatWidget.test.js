import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ChatWidget from './ChatWidget.vue'

const state = vi.hoisted(() => ({
  calls: [],
  push: vi.fn(),
  nextConversationId: 200,
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: state.push }),
}))

vi.mock('@/lib/api', () => ({
  apiRequest: vi.fn(async (path, options = {}) => {
    state.calls.push({ path, options })

    if (path === '/chatbot/conversations/') {
      return {
        conversation: { id: state.nextConversationId++ },
        messages: [
          {
            id: 1,
            role: 'assistant',
            content: 'Hola, conversación nueva.',
          },
        ],
      }
    }

    if (path === '/chatbot/history/') {
      return {
        conversation: { id: Number(options.query?.conversation_id) },
        messages: [
          {
            id: 2,
            role: 'assistant',
            content: 'Historial recuperado.',
          },
        ],
      }
    }

    if (path === '/chatbot/briefing/') {
      return { suggestions: [] }
    }

    if (path === '/chatbot/messages/') {
      return {
        messages: [
          { id: 3, role: 'user', content: options.body.content },
          { id: 4, role: 'assistant', content: 'Respuesta nueva.' },
        ],
        action: null,
      }
    }

    throw new Error('Ruta inesperada: ' + path)
  }),
}))

describe('ChatWidget conversaciones', () => {
  beforeEach(() => {
    state.calls.length = 0
    state.push.mockReset()
    state.nextConversationId = 200
    window.localStorage.clear()
  })

  it('invalida la conversación legacy y empieza una nueva', async () => {
    window.localStorage.setItem('ipac.chatbot.conversation', '99')

    const wrapper = mount(ChatWidget)
    await wrapper.get('.ipac-chat-fab').trigger('click')
    await flushPromises()

    expect(
      state.calls.some(
        (call) =>
          call.path === '/chatbot/history/' &&
          call.options.query?.conversation_id === '99',
      ),
    ).toBe(false)
    expect(
      state.calls.some((call) => call.path === '/chatbot/conversations/'),
    ).toBe(true)
    expect(window.localStorage.getItem('ipac.chatbot.conversation')).toBeNull()
    expect(
      window.localStorage.getItem('ipac.chatbot.conversation.native-tools-v1'),
    ).toBe('200')
    expect(wrapper.text()).toContain('Hola, conversación nueva.')
  })

  it('permite iniciar manualmente una nueva conversación', async () => {
    const wrapper = mount(ChatWidget)
    await wrapper.get('.ipac-chat-fab').trigger('click')
    await flushPromises()

    const firstId = window.localStorage.getItem(
      'ipac.chatbot.conversation.native-tools-v1',
    )
    expect(firstId).toBe('200')

    await wrapper.get('button[aria-label="Nueva conversación"]').trigger('click')
    await flushPromises()

    expect(
      window.localStorage.getItem('ipac.chatbot.conversation.native-tools-v1'),
    ).toBe('201')
    expect(wrapper.text()).toContain('Hola, conversación nueva.')
    expect(
      state.calls.filter((call) => call.path === '/chatbot/conversations/'),
    ).toHaveLength(2)
  })
})
