import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import MatriculasPanel from './MatriculasPanel.vue'

// El panel lee `matriculas.value` del composable, no lo que devuelve la llamada.
// Por eso el mock tiene que empezar a llenarlo: un mock que solo resuelve
// deja al panel sin matrícula activa y los botones nunca se renderizan.
const estado = vi.hoisted(() => ({ matriculas: [] }))
const rolActual = vi.hoisted(() => ({ value: 'administracion' }))

vi.mock('@/composables/useMatriculas', async () => {
  const { ref } = await import('vue')
  const matriculas = ref([])
  return {
    useMatriculas: () => ({
      matriculas,
      loading: ref(false),
      error: ref(''),
      loadMatriculas: async () => {
        matriculas.value = [...estado.matriculas]
        return matriculas.value
      },
      finalizarMatricula: vi.fn(),
    }),
  }
})

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('@/lib/swal', () => ({
  confirmFinalizarMatricula: vi.fn(),
}))

vi.mock('@/composables/useAuth', async () => {
  const { ref } = await import('vue')
  return {
    useAuth: () => ({ user: ref({ perfil: { rol: rolActual.value } }) }),
  }
})

const MATRICULA_ACTIVA = {
  id: 3,
  alumno: 12,
  carrera: 7,
  carrera_nombre: 'Técnicatura en Sistemas',
  sucursal: 1,
  sucursal_nombre: 'Posadas',
  fecha_inicio: '2026-03-01',
  estado: 'activa',
}

function montarPanel(rol = 'administracion') {
  rolActual.value = rol
  estado.matriculas = [MATRICULA_ACTIVA]
  return mount(MatriculasPanel, {
    props: {
      alumno: { id: 12, nombre: 'Ana', apellido: 'Lopez', sucursal: 1 },
      canManage: true,
    },
    global: {
      stubs: { MatriculaForm: true, ReinscripcionCuotasModal: true },
    },
  })
}

describe('MatriculasPanel', () => {
  beforeEach(() => {
    estado.matriculas = []
    rolActual.value = 'administracion'
  })

  it('explicita la ausencia de matrícula activa y ofrece crearla', async () => {
    estado.matriculas = []
    const wrapper = mount(MatriculasPanel, {
      props: {
        alumno: { id: 12, nombre: 'Ana', apellido: 'Lopez', sucursal: 1 },
        canManage: true,
      },
      global: {
        stubs: { MatriculaForm: true, ReinscripcionCuotasModal: true },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Sin matrícula activa')
    expect(wrapper.get('.matriculas-add-button').text()).toContain('Nueva matrícula')
  })

  it('sin matrícula activa no hay nada que reinscribir todavía', async () => {
    estado.matriculas = []
    const wrapper = mount(MatriculasPanel, {
      props: {
        alumno: { id: 12, nombre: 'Ana', apellido: 'Lopez', sucursal: 1 },
        canManage: true,
      },
      global: {
        stubs: { MatriculaForm: true, ReinscripcionCuotasModal: true },
      },
    })
    await flushPromises()

    expect(wrapper.find('.matricula-reinscripcion').exists()).toBe(false)
  })

  it('ofrece la reinscripción a quien puede gestionar cuotas', async () => {
    const wrapper = await montarPanel('administracion')
    await flushPromises()

    expect(wrapper.find('.matricula-reinscripcion').exists()).toBe(true)
  })

  it('tesorería también puede, porque es la misma capability que la masiva', async () => {
    const wrapper = await montarPanel('tesoreria')
    await flushPromises()

    expect(wrapper.find('.matricula-reinscripcion').exists()).toBe(true)
  })

  it('caja no ve el botón aunque pueda gestionar la matrícula', async () => {
    // Emitir cuotas no es su permiso. Si acá se gateara con canManage, el
    // botón aparecería y el backend lo rechazaría con 403.
    const wrapper = await montarPanel('caja')
    await flushPromises()

    expect(wrapper.find('.matricula-reinscripcion').exists()).toBe(false)
  })

  it('abre el modal de reinscripción sobre la matrícula activa', async () => {
    const wrapper = await montarPanel('administracion')
    await flushPromises()

    await wrapper.get('.matricula-reinscripcion').trigger('click')

    const modal = wrapper.findComponent({ name: 'ReinscripcionCuotasModal' })
    expect(modal.props('matricula')).toEqual(MATRICULA_ACTIVA)
    expect(modal.props('alumno').id).toBe(12)
  })
})
