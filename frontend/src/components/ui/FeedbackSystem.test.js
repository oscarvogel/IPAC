import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import AppButtonContent from './AppButtonContent.vue'
import AppPageState from './AppPageState.vue'
import AppToaster from './AppToaster.vue'
import { useToast } from '@/composables/useToast'

describe('sistema global de feedback', () => {
  const toast = useToast()

  beforeEach(() => {
    vi.useFakeTimers()
    toast.clearAll()
  })

  afterEach(() => {
    toast.clearAll()
    vi.useRealTimers()
  })

  it('muestra toasts accesibles, deduplica mensajes y permite cerrarlos', async () => {
    toast.success('Alumno guardado', { duration: 0 })
    toast.success('Alumno guardado', { duration: 0 })

    const wrapper = mount(AppToaster, {
      global: { stubs: { Teleport: true, TransitionGroup: false } },
    })

    expect(wrapper.findAll('.toast-message')).toHaveLength(1)
    expect(wrapper.get('[role="status"]').text()).toContain('Operación completada')
    expect(wrapper.text()).toContain('Alumno guardado')

    await wrapper.get('.toast-message-close').trigger('click')
    expect(toast.messages.value).toHaveLength(0)
  })

  it('descarta automáticamente un mensaje al terminar su duración', () => {
    toast.info('Actualizando información', { duration: 1200 })
    expect(toast.messages.value).toHaveLength(1)

    vi.advanceTimersByTime(1200)
    expect(toast.messages.value).toHaveLength(0)
  })

  it('alterna entre skeleton y error recuperable', async () => {
    const wrapper = mount(AppPageState, {
      props: { loading: true, label: 'los alumnos' },
    })

    expect(wrapper.attributes('aria-busy')).toBe('true')
    expect(wrapper.findAll('.page-state-metric')).toHaveLength(4)

    await wrapper.setProps({ loading: false, error: 'Servidor no disponible' })
    expect(wrapper.get('[role="alert"]').text()).toContain('Servidor no disponible')
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })

  it('incorpora un indicador Heroicon en botones ocupados', () => {
    const wrapper = mount(AppButtonContent, {
      props: { loading: true, label: 'Guardar', loadingLabel: 'Guardando…' },
    })

    expect(wrapper.text()).toContain('Guardando…')
    expect(wrapper.find('svg.is-spinning').exists()).toBe(true)
  })
})
