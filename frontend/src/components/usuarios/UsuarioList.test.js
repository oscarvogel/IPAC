import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UsuarioList from './UsuarioList.vue'

const usuarios = [
  {
    id: 2,
    username: 'consulta',
    first_name: 'Pedro',
    last_name: 'Silva',
    email: 'pedro@example.com',
    is_active: false,
    perfil: {
      rol: 'consulta',
      sucursal: { id: 2, nombre: 'Eldorado' },
      puede_ver_todas_las_sucursales: false,
    },
  },
  {
    id: 1,
    username: 'admin',
    first_name: 'Ana',
    last_name: 'Gómez',
    email: 'ana@example.com',
    is_active: true,
    perfil: {
      rol: 'superadmin',
      sucursal: { id: 1, nombre: 'Posadas' },
      puede_ver_todas_las_sucursales: true,
    },
  },
]

describe('directorio de usuarios', () => {
  it('prioriza usuarios activos y representa rol y alcance', () => {
    const wrapper = mount(UsuarioList, { props: { usuarios } })
    const rows = wrapper.findAll('tbody tr')

    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('admin')
    expect(rows[0].text()).toContain('Superadmin')
    expect(rows[0].text()).toContain('Todas las sedes')
    expect(rows[1].text()).toContain('Sede asignada')
  })

  it('mantiene edición y limita la desactivación a usuarios activos', async () => {
    const wrapper = mount(UsuarioList, { props: { usuarios } })
    const rows = wrapper.findAll('tbody tr')

    await rows[0].get('button[aria-label="Editar usuario"]').trigger('click')
    expect(wrapper.emitted('edit')[0][0]).toEqual(usuarios[1])

    const deactivateButtons = wrapper.findAll('button[aria-label="Desactivar usuario"]')
    expect(deactivateButtons).toHaveLength(1)
    await deactivateButtons[0].trigger('click')
    expect(wrapper.emitted('deactivate')[0][0]).toEqual(usuarios[1])
  })
})
