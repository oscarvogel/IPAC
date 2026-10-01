import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import CarreraList from './CarreraList.vue'

const conDesglose = {
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
}

const sinDesglose = {
  id: 2,
  nombre: 'Curso de Diseño',
  tipo: 'curso',
  sucursal: 2,
  sucursal_nombre: 'Eldorado',
  plan_cuotas: null,
  cuota_total: null,
  cuota_programatica: null,
  cuota_extraprogramatica: null,
  activa: false,
}

// Solo una de las dos partes cargadas: el reparto no se puede derivar, asi que
// la cuota tiene que aparecer como "sin desglose".
const desgloseIncompleto = {
  id: 3,
  nombre: 'Tecnicatura en Sistemas',
  tipo: 'carrera',
  sucursal: 1,
  sucursal_nombre: 'Posadas',
  plan_cuotas: 8,
  cuota_total: '40000.00',
  cuota_programatica: '40000.00',
  cuota_extraprogramatica: null,
  activa: true,
}

function mountList(props) {
  return mount(CarreraList, {
    props,
    global: { stubs: { TransitionGroup: false } },
  })
}

describe('catálogo de carreras y cursos', () => {
  it('ordena las carreras y mantiene disponible la edición', async () => {
    const wrapper = mountList({ carreras: [conDesglose, sinDesglose] })
    const rows = wrapper.findAll('.careers-table tbody tr')

    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('Analista en Contadores')

    await rows[0].get('button[aria-label="Editar carrera"]').trigger('click')
    expect(wrapper.emitted('edit')[0][0]).toEqual(conDesglose)
  })

  it('muestra el reparto programático y extraprogramático cuando está cargado', () => {
    const wrapper = mountList({ carreras: [conDesglose] })
    const texto = wrapper.find('.careers-table tbody tr').text()

    expect(texto).toContain('Programática')
    expect(texto).toContain('Extraprogramática')
    expect(texto).toContain('62.000,00')
    expect(texto).toContain('20.000,00')
    expect(wrapper.find('.careers-table .careers-missing').exists()).toBe(false)
  })

  it('advierte cuando la carrera no puede desglosarse', () => {
    const wrapper = mountList({ carreras: [sinDesglose, desgloseIncompleto] })
    const faltantes = wrapper.findAll('.careers-table .careers-missing')

    // Sin ninguna parte y con una sola parte: en los dos casos el recibo sale
    // sin reparto, asi que hay que marcarlo.
    expect(faltantes).toHaveLength(2)
    expect(faltantes[0].text()).toContain('Sin desglose')
  })

  it('ofrece desactivar solamente las carreras activas', async () => {
    const wrapper = mountList({ carreras: [conDesglose, sinDesglose] })
    const botones = wrapper.findAll('.careers-table button[aria-label="Desactivar carrera"]')

    expect(botones).toHaveLength(1)
    await botones[0].trigger('click')
    expect(wrapper.emitted('deactivate')[0][0]).toEqual(conDesglose)
  })

  it('ofrece tarjetas móviles con el desglose y acciones equivalentes', async () => {
    const wrapper = mountList({ carreras: [conDesglose, sinDesglose] })
    const cards = wrapper.findAll('.careers-mobile-list .mobile-record-card')

    expect(cards).toHaveLength(2)
    expect(cards[0].text()).toContain('Analista en Contadores')
    expect(cards[0].text()).toContain('Programática')
    expect(cards[1].text()).toContain('Sin desglose')

    await cards[0].get('.mobile-action-trigger').trigger('click')
    await cards[0].get('.mobile-action-popover button').trigger('click')
    expect(wrapper.emitted('edit')[0][0]).toEqual(conDesglose)
  })

  it('distingue el estado vacío inicial del filtrado sin resultados', () => {
    const inicial = mountList({ carreras: [] })
    expect(inicial.text()).toContain('Todavía no hay carreras cargadas')

    const filtrado = mountList({ carreras: [], filtered: true })
    expect(filtrado.text()).toContain('No encontramos carreras')
  })
})