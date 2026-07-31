import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SucursalList from './SucursalList.vue'

const sucursales = [
  { id: 2, codigo: 'ELD', nombre: 'Eldorado', activa: false },
  { id: 1, codigo: 'POS', nombre: 'Posadas', activa: true },
]

const carreras = [
  { id: 1, nombre: 'Administración', sucursal: 1 },
  { id: 2, nombre: 'Contabilidad', sucursal: 1 },
  { id: 3, nombre: 'Informática', sucursal: 2 },
]

describe('directorio de sucursales', () => {
  it('prioriza las sedes activas y muestra su oferta académica', () => {
    const wrapper = mount(SucursalList, { props: { sucursales, carreras } })
    const cards = wrapper.findAll('.branch-card')

    expect(cards).toHaveLength(2)
    expect(cards[0].text()).toContain('Posadas')
    expect(cards[0].text()).toContain('2 carreras')
    expect(cards[1].text()).toContain('Eldorado')
    expect(cards[1].text()).toContain('1 carrera')
  })

  it('mantiene la edición y limita la desactivación a sedes activas', async () => {
    const wrapper = mount(SucursalList, { props: { sucursales, carreras } })
    const cards = wrapper.findAll('.branch-card')

    await cards[0].findAll('button')[0].trigger('click')
    expect(wrapper.emitted('edit')[0][0]).toEqual(sucursales[1])

    const deactivateButtons = wrapper.findAll('.branch-card-actions .deactivate')
    expect(deactivateButtons).toHaveLength(1)
    await deactivateButtons[0].trigger('click')
    expect(wrapper.emitted('deactivate')[0][0]).toEqual(sucursales[1])
  })
})
