import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import CarreraForm from './CarreraForm.vue'

const createCarrera = vi.hoisted(() => vi.fn().mockResolvedValue({ id: 1 }))
const updateCarrera = vi.hoisted(() => vi.fn().mockResolvedValue({ id: 1 }))

vi.mock('@/composables/useCarreras', () => ({
  useCarreras: () => ({ createCarrera, updateCarrera }),
}))

vi.mock('@/composables/useCatalogos', () => ({
  useCatalogos: () => ({ sucursales: ref([{ id: 1, nombre: 'Posadas' }]) }),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

function montar(carrera = null) {
  return mount(CarreraForm, {
    props: { open: true, carrera },
    global: { stubs: { Teleport: true } },
  })
}

// Los inputs van envueltos en su label, asi que se localizan por el texto del
// label en vez de por posicion: agregar un campo no rompe el test.
function campo(wrapper, etiqueta) {
  const label = wrapper.findAll('label').find((item) => item.text().includes(etiqueta))
  if (!label) throw new Error(`no se encontro el campo "${etiqueta}"`)
  return label.get('input')
}

const NOMBRE = 'Ej. Tecnicatura en Sistemas'
const MATRICULA = 'Importe de matrícula'
const PROGRAMATICA = 'Cuota programática'
const EXTRAPROGRAMATICA = 'Cuota extraprogramática'
const TOTAL = 'Cuota total'

const AVISO_SIN_DESGLOSE = 'Mientras falte una, los recibos de esta carrera se'

describe('formulario de carrera', () => {
  beforeEach(() => vi.clearAllMocks())

  it('calcula la cuota total sumando las dos partes del desglose', async () => {
    const wrapper = montar()

    await campo(wrapper, PROGRAMATICA).setValue('62000')
    await campo(wrapper, EXTRAPROGRAMATICA).setValue('20000')
    await wrapper.vm.$nextTick()

    expect(campo(wrapper, TOTAL).element.value).toBe('82000')
    expect(wrapper.text()).toContain('Calculado como la suma de las dos partes')
  })

  it('recalcula el total si se ajusta una de las partes', async () => {
    const wrapper = montar()

    await campo(wrapper, PROGRAMATICA).setValue('62000')
    await campo(wrapper, EXTRAPROGRAMATICA).setValue('20000')
    await wrapper.vm.$nextTick()
    expect(campo(wrapper, TOTAL).element.value).toBe('82000')

    await campo(wrapper, EXTRAPROGRAMATICA).setValue('25000')
    await wrapper.vm.$nextTick()
    expect(campo(wrapper, TOTAL).element.value).toBe('87000')
  })

  it('respeta un total cargado a mano y avisa si no coincide con la suma', async () => {
    const wrapper = montar()

    await campo(wrapper, PROGRAMATICA).setValue('62000')
    await campo(wrapper, EXTRAPROGRAMATICA).setValue('20000')
    await wrapper.vm.$nextTick()
    await campo(wrapper, TOTAL).setValue('90000')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Valor cargado a mano')
    expect(wrapper.text()).toContain('no coincide con la cuota total')
  })

  it('avisa mientras falte una de las dos partes del desglose', async () => {
    const wrapper = montar()

    await campo(wrapper, PROGRAMATICA).setValue('62000')
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain(AVISO_SIN_DESGLOSE)

    await campo(wrapper, EXTRAPROGRAMATICA).setValue('20000')
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).not.toContain(AVISO_SIN_DESGLOSE)
  })

  it('envía el desglose completo al crear una carrera', async () => {
    const wrapper = montar()

    await wrapper.find(`input[placeholder="${NOMBRE}"]`).setValue('Tecnicatura en Sistemas')
    await campo(wrapper, MATRICULA).setValue('35000')
    await campo(wrapper, PROGRAMATICA).setValue('62000')
    await campo(wrapper, EXTRAPROGRAMATICA).setValue('20000')
    await wrapper.vm.$nextTick()

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createCarrera).toHaveBeenCalledWith(
      expect.objectContaining({
        nombre: 'Tecnicatura en Sistemas',
        tipo: 'carrera',
        sucursal: 1,
        importe_matricula: 35000,
        cuota_programatica: 62000,
        cuota_extraprogramatica: 20000,
        cuota_total: 82000,
      }),
    )
  })

  it('carga los valores guardados al editar y no pisa un total que no es la suma', async () => {
    const wrapper = montar({
      id: 4,
      nombre: 'Analista en Sistemas',
      tipo: 'curso',
      sucursal: 1,
      duracion: '2 años',
      descripcion: 'Plan de seis meses',
      plan_cuotas: 8,
      importe_matricula: '20000.00',
      cuota_programatica: '30000.00',
      cuota_extraprogramatica: '10000.00',
      cuota_total: '45000.00',
      cuota_convenio_20: '28000.00',
      cuota_convenio_15: '29250.00',
      activa: true,
    })

    expect(wrapper.find(`input[placeholder="${NOMBRE}"]`).element.value)
      .toBe('Analista en Sistemas')
    expect(campo(wrapper, 'Cantidad de cuotas').element.value).toBe('8')
    expect(campo(wrapper, TOTAL).element.value).toBe('45000.00')
    expect(wrapper.text()).toContain('Valor cargado a mano')

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(updateCarrera).toHaveBeenCalledWith(
      4,
      expect.objectContaining({
        cuota_total: 45000,
        cuota_programatica: 30000,
        cuota_extraprogramatica: 10000,
        plan_cuotas: 8,
        activa: true,
      }),
    )
  })

  it('deja el checkbox de activa solo en la edición', async () => {
    expect(montar().find('.checkbox-inline').exists()).toBe(false)

    const edicion = montar({
      id: 4,
      nombre: 'Analista en Sistemas',
      tipo: 'carrera',
      sucursal: 1,
      cuota_programatica: '30000.00',
      cuota_extraprogramatica: '10000.00',
      cuota_total: '40000.00',
      activa: true,
    })
    expect(edicion.find('.checkbox-inline input[type="checkbox"]').element.checked).toBe(true)
  })
})