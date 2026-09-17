import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ConceptoList from './conceptos/ConceptoList.vue'
import UsuarioList from './usuarios/UsuarioList.vue'

const conceptos = Array.from({ length: 30 }, (_, index) => ({
  id: index + 1,
  nombre: `Concepto ${String(index + 1).padStart(2, '0')}`,
  tipo: 'cuota',
  importe: 25000,
  sucursal_nombre: 'Posadas',
  carrera_nombre: null,
  activo: true,
}))

const usuarios = Array.from({ length: 30 }, (_, index) => ({
  id: index + 1,
  username: `usuario${String(index + 1).padStart(2, '0')}`,
  first_name: 'Usuario',
  last_name: `${index + 1}`,
  email: `usuario${index + 1}@example.com`,
  is_active: true,
  perfil: {
    rol: 'consulta',
    sucursal: { id: 1, nombre: 'Posadas' },
    puede_ver_todas_las_sucursales: false,
  },
}))

const waitForMotion = () => new Promise((resolve) => setTimeout(resolve, 240))

describe('paginacion de catalogos', () => {
  const mountList = (component, props) => mount(component, {
    props,
    global: { stubs: { TransitionGroup: false } },
  })

  it('limita Conceptos a 25 registros, navega y reinicia al cambiar resultados', async () => {
    const wrapper = mountList(ConceptoList, { conceptos })

    expect(wrapper.findAll('tbody tr')).toHaveLength(25)
    expect(wrapper.findAll('.concepts-mobile-list .mobile-record-card')).toHaveLength(25)

    await wrapper.findAll('.catalog-pagination button')[1].trigger('click')
    await waitForMotion()
    expect(wrapper.findAll('tbody tr')).toHaveLength(5)

    await wrapper.setProps({ conceptos: conceptos.slice(0, 3) })
    await waitForMotion()
    expect(wrapper.findAll('tbody tr')).toHaveLength(3)
  })

  it('limita Usuarios a 25 registros y conserva el contador total', async () => {
    const wrapper = mountList(UsuarioList, { usuarios })

    expect(wrapper.find('.users-list-count').text()).toContain('30 usuarios')
    expect(wrapper.findAll('tbody tr')).toHaveLength(25)
    expect(wrapper.findAll('.users-mobile-list .mobile-record-card')).toHaveLength(25)

    await wrapper.findAll('.catalog-pagination button')[1].trigger('click')
    await waitForMotion()
    expect(wrapper.findAll('tbody tr')).toHaveLength(5)
    expect(wrapper.get('.catalog-pagination').text()).toContain('Página 2 de 2')
  })
})
