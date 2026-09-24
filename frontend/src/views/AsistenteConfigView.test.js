import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AsistenteConfigView from './AsistenteConfigView.vue'

const state = vi.hoisted(() => ({
  role: 'administracion',
  api: {
    listKnowledge: vi.fn(async () => ({ results: [] })),
    createKnowledge: vi.fn(),
    updateKnowledge: vi.fn(),
    activateKnowledge: vi.fn(),
    deactivateKnowledge: vi.fn(),
    listUnresolved: vi.fn(async () => ({ results: [] })),
    resolveUnresolved: vi.fn(),
    ignoreUnresolved: vi.fn(),
    createArticleFromUnresolved: vi.fn(),
    getConfig: vi.fn(async () => ({
      email_habilitado: false,
      modo_email: 'desactivado',
      destinatarios: [],
      incluir_fuera_de_alcance: false,
      hora_resumen_diario: '18:00:00',
    })),
    updateConfig: vi.fn(),
  },
}))

vi.mock('@/composables/useAssistantAdmin', () => ({
  useAssistantAdmin: () => state.api,
}))

vi.mock('@/composables/useAuth', () => ({
  useAuth: () => ({
    can: (capability) => (
      state.role === 'superadmin'
        ? ['manage-assistant', 'configure-assistant-notifications'].includes(capability)
        : capability === 'manage-assistant'
    ),
  }),
}))

function tab(wrapper, label) {
  return wrapper.findAll('.tabs button').find((button) => button.text().includes(label))
}

describe('AsistenteConfigView', () => {
  beforeEach(() => {
    state.role = 'administracion'
    vi.clearAllMocks()
  })

  it('muestra conocimiento, no resueltas y notificaciones', async () => {
    const wrapper = mount(AsistenteConfigView)
    await flushPromises()

    expect(wrapper.text()).toContain('Base de conocimiento')
    expect(wrapper.text()).toContain('Consultas no resueltas')
    expect(wrapper.text()).toContain('Notificaciones')
  })

  it('deja notificaciones en solo lectura para Administración', async () => {
    const wrapper = mount(AsistenteConfigView)
    await flushPromises()
    await tab(wrapper, 'Notificaciones').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-testid="assistant-email-mode"]').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Sólo Superadmin')
  })

  it('permite editar notificaciones al Superadmin', async () => {
    state.role = 'superadmin'
    const wrapper = mount(AsistenteConfigView)
    await flushPromises()
    await tab(wrapper, 'Notificaciones').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-testid="assistant-email-mode"]').attributes('disabled')).toBeUndefined()
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
  })
})
