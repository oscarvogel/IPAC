import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import MovimientoForm from './MovimientoForm.vue'

const cajaHoy = { id: 4, sucursal_nombre: 'Posadas', fecha: '2026-10-01', estado: 'abierta' }
const receptores = [
  { id: 21, username: 'zulma', rol: 'caja', rol_label: 'Caja' },
  { id: 22, username: 'laura', rol: 'caja', rol_label: 'Caja' },
]

function montar(props = {}) {
  return mount(MovimientoForm, {
    props: { open: true, cajaHoy, loading: false, tipoInicial: 'egreso', receptores, ...props },
    global: { stubs: { Teleport: true } },
  })
}

function selectTipo(wrapper) {
  return wrapper.findAll('select').at(0)
}

// El select de receptor solo existe cuando el tipo lo exige, asi que se localiza
// por sus opciones en lugar de por posicion.
function selectReceptor(wrapper) {
  return wrapper.findAll('select').find((select) =>
    select.findAll('option').some((option) => option.attributes('value') === '21'),
  )
}

async function elegirTipo(wrapper, tipo) {
  await selectTipo(wrapper).setValue(tipo)
}

async function completar(wrapper, { descripcion = 'Pase a Laura' } = {}) {
  await wrapper.find('input[type="number"]').setValue('500.00')
  await wrapper.findAll('input').at(1).setValue(descripcion)
}

describe('MovimientoForm', () => {
  beforeEach(() => vi.clearAllMocks())

  it('no pide conformidad para los movimientos corrientes', async () => {
    const wrapper = montar()
    expect(wrapper.text()).not.toContain('Recibe el dinero')

    await elegirTipo(wrapper, 'ingreso')
    expect(wrapper.text()).not.toContain('Recibe el dinero')
    expect(selectReceptor(wrapper)).toBeUndefined()
  })

  it('exige indicar quien recibe cuando el movimiento es un pase o un retiro', async () => {
    const wrapper = montar()

    await elegirTipo(wrapper, 'pase')
    expect(wrapper.text()).toContain('Recibe el dinero')
    expect(wrapper.text()).toContain('zulma')

    await elegirTipo(wrapper, 'retiro')
    expect(wrapper.text()).toContain('Recibe el dinero')

    await elegirTipo(wrapper, 'egreso')
    expect(wrapper.text()).not.toContain('Recibe el dinero')
  })

  it('envia el receptor del pase para que el comprobante quede auditable', async () => {
    const wrapper = montar()
    await elegirTipo(wrapper, 'pase')
    await completar(wrapper)

    await selectReceptor(wrapper).setValue('22')

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')[0][0]).toEqual({
      caja: 4,
      tipo: 'pase',
      medio: 'efectivo',
      importe: 500,
      descripcion: 'Pase a Laura',
      recibido_por: 22,
    })
  })

  it('envia el receptor en el retiro, que tambien mueve plata', async () => {
    const wrapper = montar()
    await elegirTipo(wrapper, 'retiro')
    await completar(wrapper, { descripcion: 'Retiro para traslado' })
    await selectReceptor(wrapper).setValue('21')

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    const payload = wrapper.emitted('submit')[0][0]
    expect(payload.tipo).toBe('retiro')
    expect(payload.recibido_por).toBe(21)
  })

  it('no manda receptor en un ingreso corriente', async () => {
    const wrapper = montar()
    await elegirTipo(wrapper, 'ingreso')
    await completar(wrapper, { descripcion: 'Donacion' })

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    const payload = wrapper.emitted('submit')[0][0]
    expect(payload.tipo).toBe('ingreso')
    expect(payload.recibido_por).toBeNull()
  })

  it('limpia el receptor cuando se reabre el formulario', async () => {
    const wrapper = montar()
    await elegirTipo(wrapper, 'pase')
    await selectReceptor(wrapper).setValue('22')
    await completar(wrapper)

    await wrapper.setProps({ open: false })
    await wrapper.setProps({ open: true })
    await elegirTipo(wrapper, 'pase')

    expect(selectReceptor(wrapper).element.value).toBe('')
  })
})