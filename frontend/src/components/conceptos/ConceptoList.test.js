import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ConceptoList from './ConceptoList.vue'

const conceptos = [
  {
    id: 2,
    nombre: 'Matrícula anual',
    tipo: 'matricula',
    importe: 50000,
    sucursal_nombre: 'Posadas',
    carrera_nombre: null,
    activo: true,
  },
  {
    id: 1,
    nombre: 'Cuota mensual',
    tipo: 'cuota',
    importe: 25000,
    sucursal_nombre: 'Eldorado',
    carrera_nombre: 'Administración',
    activo: false,
  },
]

describe('catálogo de conceptos', () => {
  it('ordena los conceptos y mantiene disponible la edición', async () => {
    const wrapper = mount(ConceptoList, { props: { conceptos } })
    const rows = wrapper.findAll('tbody tr')

    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('Cuota mensual')

    await rows[0].get('button[aria-label="Editar concepto"]').trigger('click')
    expect(wrapper.emitted('edit')[0][0]).toEqual(conceptos[1])
  })

  it('ofrece desactivar solamente los conceptos activos', async () => {
    const wrapper = mount(ConceptoList, { props: { conceptos } })
    const deactivateButtons = wrapper.findAll('.concepts-table button[aria-label="Desactivar concepto"]')

    expect(deactivateButtons).toHaveLength(1)
    await deactivateButtons[0].trigger('click')
    expect(wrapper.emitted('deactivate')[0][0]).toEqual(conceptos[0])
  })

  it('ofrece tarjetas móviles con acciones contextuales equivalentes', async () => {
    const wrapper = mount(ConceptoList, { props: { conceptos } })
    const cards = wrapper.findAll('.concepts-mobile-list .mobile-record-card')

    expect(cards).toHaveLength(2)
    expect(cards[0].text()).toContain('Cuota mensual')

    await cards[1].get('.mobile-action-trigger').trigger('click')
    await cards[1].get('.mobile-action-popover .danger').trigger('click')
    expect(wrapper.emitted('deactivate').at(-1)[0]).toEqual(conceptos[0])
  })
})
