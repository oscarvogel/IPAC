import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UnresolvedList from './UnresolvedList.vue'

const event = {
  id: 1,
  pregunta: '¿Cómo refinancio una cuota?',
  categoria: 'no_documentada',
  estado: 'pendiente',
  usuario: 'admin',
  sucursal: 'Posadas',
  respuesta: 'No tengo información suficiente.',
  creado: '2026-09-24T14:00:00-03:00',
}

describe('UnresolvedList', () => {
  it('permite convertir una consulta pendiente en artículo', async () => {
    const wrapper = mount(UnresolvedList, {
      props: { items: [event] },
    })

    await wrapper.get('[data-testid="create-article-1"]').trigger('click')

    expect(wrapper.emitted('create-article')[0][0]).toEqual(event)
  })

  it('no ofrece acciones de edición para una consulta resuelta', () => {
    const wrapper = mount(UnresolvedList, {
      props: { items: [{ ...event, estado: 'resuelta', articulo_titulo: 'Refinanciar cuotas' }] },
    })

    expect(wrapper.find('[data-testid="create-article-1"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Resuelta con: Refinanciar cuotas')
  })
})
