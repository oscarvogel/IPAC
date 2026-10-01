import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { computed, ref } from 'vue'
import CarrerasView from '@/views/CarrerasView.vue'

const authState = { rol: 'administracion', capabilities: ['manage-careers'] }
const deactivateCarrera = vi.hoisted(() => vi.fn().mockResolvedValue({}))

const carreras = [
  {
    id: 1,
    nombre: 'Analista en Contadores',
    tipo: 'carrera',
    sucursal: 1,
    sucursal_nombre: 'Posadas',
    plan_cuotas: 10,
    cuota_total: '82000.00',
    cuota_programatica: '62000.00',
    cuota_extraprogramatica: '20000.00',
    activa: true,
  },
  {
    id: 2,
    nombre: 'Curso de Diseño',
    tipo: 'curso',
    sucursal: 2,
    sucursal_nombre: 'Eldorado',
    plan_cuotas: null,
    cuota_total: null,
    cuota_programatica: null,
    cuota_extraprogramatica: null,
    activa: true,
  },
  {
    id: 3,
    nombre: 'Tecnicatura en Sistemas',
    tipo: 'carrera',
    sucursal: 1,
    sucursal_nombre: 'Posadas',
    plan_cuotas: 8,
    cuota_total: '40000.00',
    cuota_programatica: '40000.00',
    cuota_extraprogramatica: null,
    activa: false,
  },
]

vi.mock('@/composables/useCarreras', () => ({
  useCarreras: () => ({
    carreras: ref(carreras),
    error: ref(''),
    loadCarreras: vi.fn().mockResolvedValue(undefined),
    deactivateCarrera,
  }),
}))

vi.mock('@/composables/useCatalogos', () => ({
  useCatalogos: () => ({
    sucursales: ref([{ id: 1, nombre: 'Posadas' }, { id: 2, nombre: 'Eldorado' }]),
    loadCatalogo: vi.fn().mockResolvedValue(undefined),
    loadCatalogos: vi.fn().mockResolvedValue(undefined),
  }),
}))

vi.mock('@/composables/useAuth', () => ({
  useAuth: () => ({
    user: computed(() => ({ perfil: { rol: authState.rol } })),
    can: (capability) => authState.capabilities.includes(capability),
  }),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

function montar() {
  return mount(CarrerasView, {
    global: {
      stubs: {
        Teleport: true,
        CarreraList: {
          name: 'CarreraList',
          props: ['carreras'],
          template: '<div data-stub="lista" />',
        },
        CarreraForm: {
          name: 'CarreraForm',
          props: ['open', 'carrera'],
          template: '<div data-stub="form" />',
        },
      },
    },
  })
}

describe('pantalla de carreras y cursos', () => {
  beforeEach(() => {
    authState.rol = 'administracion'
    authState.capabilities = ['manage-careers']
    vi.clearAllMocks()
  })

  it('advierte cuantas carreras se emiten sin desglose', async () => {
    const wrapper = montar()
    await flushPromises()

    const aviso = wrapper.find('.careers-alert')
    expect(aviso.exists()).toBe(true)
    // Sin ninguna parte, y con una sola parte: en los dos casos no hay reparto.
    expect(aviso.text()).toContain('2 carreras sin desglose')
    expect(aviso.text()).toContain('Ministerio de Educación')
  })

  it('ofrece corregir la primera carrera sin desglose desde el aviso', async () => {
    const wrapper = montar()
    await flushPromises()

    await wrapper.find('.careers-alert button').trigger('click')

    expect(wrapper.find('[data-stub="form"]').exists()).toBe(true)
  })

  it('oculta el aviso cuando todas las carreras pueden desglosarse', async () => {
    carreras[1].cuota_programatica = '10000.00'
    carreras[1].cuota_extraprogramatica = '5000.00'
    carreras[2].cuota_extraprogramatica = '0.00'

    const wrapper = montar()
    await flushPromises()
    expect(wrapper.find('.careers-alert').exists()).toBe(false)

    carreras[1].cuota_programatica = null
    carreras[1].cuota_extraprogramatica = null
    carreras[2].cuota_extraprogramatica = null
  })

  it('reserva el alta y la edicion a quien puede administrar carreras', async () => {
    const admin = montar()
    await flushPromises()
    expect(admin.find('.careers-primary-action').exists()).toBe(true)

    authState.capabilities = []
    const consulta = montar()
    await flushPromises()
    expect(consulta.find('.careers-primary-action').exists()).toBe(false)
  })

  it('filtra por sucursal y por tipo', async () => {
    const wrapper = montar()
    await flushPromises()

    const nombres = () => wrapper
      .findComponent({ name: 'CarreraList' })
      .props('carreras')
      .map((carrera) => carrera.nombre)

    const selects = wrapper.findAll('.careers-toolbar select')

    await selects[0].setValue('2')
    await wrapper.vm.$nextTick()
    expect(nombres()).toEqual(['Curso de Diseño'])

    await selects[1].setValue('carrera')
    await wrapper.vm.$nextTick()
    expect(nombres()).toEqual([])

    await selects[0].setValue('todas')
    await selects[1].setValue('carrera')
    await wrapper.vm.$nextTick()
    expect(nombres()).toEqual(['Analista en Contadores', 'Tecnicatura en Sistemas'])
  })
})