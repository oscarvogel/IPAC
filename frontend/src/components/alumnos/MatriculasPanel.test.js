import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import MatriculasPanel from './MatriculasPanel.vue'

const loadMatriculas = vi.hoisted(() => vi.fn().mockResolvedValue([]))

vi.mock('@/composables/useMatriculas', () => ({
  useMatriculas: () => ({
    matriculas: ref([]),
    loading: ref(false),
    error: ref(''),
    loadMatriculas,
    finalizarMatricula: vi.fn(),
  }),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('@/lib/swal', () => ({
  confirmFinalizarMatricula: vi.fn(),
}))

describe('MatriculasPanel', () => {
  it('explicita la ausencia de matrícula activa y ofrece crearla', async () => {
    const wrapper = mount(MatriculasPanel, {
      props: {
        alumno: { id: 12, nombre: 'Ana', apellido: 'Lopez', sucursal: 1 },
        canManage: true,
      },
      global: {
        stubs: { MatriculaForm: true },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Sin matrícula activa')
    expect(wrapper.get('.matriculas-add-button').text()).toContain('Nueva matrícula')
    expect(loadMatriculas).toHaveBeenCalledWith(12)
  })
})
