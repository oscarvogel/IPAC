import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import MatriculaForm from './MatriculaForm.vue'

const createMatricula = vi.hoisted(() => vi.fn().mockResolvedValue({ id: 8 }))
const updateMatricula = vi.hoisted(() => vi.fn().mockResolvedValue({ id: 4 }))

vi.mock('@/composables/useCatalogos', () => ({
  useCatalogos: () => ({
    carreras: ref([{ id: 7, sucursal: 1, nombre: 'Administración contable' }]),
  }),
}))

vi.mock('@/composables/useMatriculas', () => ({
  useMatriculas: () => ({ createMatricula, updateMatricula }),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

const alumno = { id: 12, nombre: 'Ana', apellido: 'López', sucursal: 1 }

function mountForm(matricula = null) {
  return mount(MatriculaForm, {
    props: { open: true, alumno, matricula },
    global: {
      stubs: { Teleport: true },
    },
  })
}

describe('MatriculaForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('crea una matrícula activa sin mostrar ni permitir fecha de fin', async () => {
    const wrapper = mountForm()

    expect(wrapper.text()).not.toContain('Fecha de fin')
    await wrapper.get('select').setValue('7')
    await wrapper.get('input[type="date"]').setValue('2026-08-17')
    await wrapper.get('textarea').setValue('Observación de prueba')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createMatricula).toHaveBeenCalledWith({
      alumno: 12,
      carrera: 7,
      estado: 'activa',
      fecha_inicio: '2026-08-17',
      fecha_fin: null,
      observacion: 'Observación de prueba',
    })
  })

  it('al editar no envía fecha de fin aunque la matrícula ya esté finalizada', async () => {
    const wrapper = mountForm({
      id: 4,
      carrera: 7,
      carrera_nombre: 'Administración contable',
      fecha_inicio: '2026-03-01',
      fecha_fin: '2026-08-17',
      observacion: 'Historial',
      estado: 'finalizada',
    })

    expect(wrapper.text()).not.toContain('Fecha de fin')
    await wrapper.get('textarea').setValue('Observación actualizada')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(updateMatricula).toHaveBeenCalledWith(4, {
      fecha_inicio: '2026-03-01',
      observacion: 'Observación actualizada',
    })
  })
})
