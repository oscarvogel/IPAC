import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ChatWidget from './ChatWidget.vue'

const state = vi.hoisted(() => ({
  messageResponses: [],
  calls: [],
  push: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: state.push }),
}))

vi.mock('@/lib/api', () => ({
  apiRequest: vi.fn(async (path, options = {}) => {
    state.calls.push({ path, options })
    if (path === '/chatbot/conversations/') {
      return {
        conversation: { id: 10 },
        messages: [{ id: 1, role: 'assistant', content: 'Hola, soy el Asistente IPAC.' }],
      }
    }
    if (path === '/chatbot/briefing/') return { suggestions: [] }
    if (path === '/chatbot/history/') throw new Error('sin conversación almacenada')
    if (path === '/chatbot/messages/') return state.messageResponses.shift()
    throw new Error('Ruta inesperada: ' + path)
  }),
}))

async function openAndSend(wrapper, text) {
  await wrapper.get('.ipac-chat-fab').trigger('click')
  await flushPromises()
  await wrapper.get('#ipac-chat-input').setValue(text)
  await wrapper.get('.ipac-chat-compose').trigger('submit')
  await flushPromises()
}

describe('ChatWidget fase 2', () => {
  beforeEach(() => {
    state.calls.length = 0
    state.messageResponses.length = 0
    state.push.mockReset()
    window.localStorage.clear()
  })

  it('muestra una respuesta de datos reales', async () => {
    state.messageResponses.push({
      source: 'tool',
      messages: [
        { id: 2, role: 'user', content: '¿cuánto es la deuda total?' },
        {
          id: 3,
          role: 'assistant',
          content: 'La deuda pendiente es de $ 1.250.000,00. Alcance: Posadas.',
        },
      ],
      action: null,
      clarification: null,
    })
    const wrapper = mount(ChatWidget)

    await openAndSend(wrapper, '¿cuánto es la deuda total?')

    expect(wrapper.text()).toContain('La deuda pendiente')
    expect(wrapper.text()).toContain('Alcance: Posadas')
  })

  it('muestra el rechazo controlado para temas ajenos a IPAC', async () => {
    state.messageResponses.push({
      source: 'out_of_scope',
      messages: [
        { id: 2, role: 'user', content: '¿cómo se cura la gripe?' },
        {
          id: 3,
          role: 'assistant',
          content: 'Mi función está limitada al sistema IPAC. No puedo responder consultas generales sobre salud, noticias u otros temas.',
        },
      ],
      action: null,
      clarification: null,
    })
    const wrapper = mount(ChatWidget)

    await openAndSend(wrapper, '¿cómo se cura la gripe?')

    expect(wrapper.text()).toContain('limitada al sistema IPAC')
  })

  it('envía selected_alumno_id al elegir un candidato ambiguo', async () => {
    state.messageResponses.push(
      {
        source: 'tool',
        messages: [
          { id: 2, role: 'user', content: '¿cuánto debe Juan Perez?' },
          { id: 3, role: 'assistant', content: 'Encontré más de un alumno que coincide.' },
        ],
        action: null,
        clarification: {
          candidates: [
            { id: 91, nombre: 'Perez, Juan', legajo: 'P-91', sucursal: 'Posadas' },
            { id: 92, nombre: 'Perez, Juan', legajo: 'E-92', sucursal: 'Eldorado' },
          ],
        },
      },
      {
        source: 'tool',
        messages: [
          { id: 4, role: 'user', content: 'Consultar estado de cuenta de Perez, Juan' },
          { id: 5, role: 'assistant', content: 'Perez, Juan tiene una deuda pendiente de $ 700,00.' },
        ],
        action: null,
        clarification: null,
      },
    )
    const wrapper = mount(ChatWidget)

    await openAndSend(wrapper, '¿cuánto debe Juan Perez?')
    const candidates = wrapper.findAll('.ipac-chat-candidates button')
    expect(candidates).toHaveLength(2)

    await candidates[0].trigger('click')
    await flushPromises()

    const messageCalls = state.calls.filter((call) => call.path === '/chatbot/messages/')
    expect(messageCalls.at(-1).options.body.selected_alumno_id).toBe(91)
    expect(wrapper.text()).toContain('deuda pendiente de $ 700,00')
  })
})
