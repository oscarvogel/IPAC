import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AlumnoList from './AlumnoList.vue'

const alumnos = [
  {
    id: 2,
    nombre: 'Pedro',
    apellido: 'Silva',
    legajo: 'A-002',
    carrera_nombre: 'Administración',
    sucursal_nombre: 'Posadas',
    estado: 'activo',
  },
  {
    id: 1,
    nombre: 'Ana',
    apellido: 'Gómez',
    legajo: 'A-001',
    carrera_nombre: 'Contabilidad',
    sucursal_nombre: 'Eldorado',
    estado: 'inactivo',
  },
]

describe('directorio de alumnos', () => {
  it('ordena alfabéticamente, marca la selección y emite el alumno elegido', async () => {
    const wrapper = mount(AlumnoList, {
      props: { alumnos, selectedAlumno: alumnos[1] },
    })
    const rows = wrapper.findAll('.students-row')

    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('Gómez, Ana')
    expect(rows[0].classes()).toContain('selected')
    expect(rows[0].attributes('aria-pressed')).toBe('true')

    await rows[1].trigger('click')
    expect(wrapper.emitted('select')[0][0]).toEqual(alumnos[0])
  })

  it('muestra una orientación útil cuando el filtro no devuelve resultados', () => {
    const wrapper = mount(AlumnoList, { props: { alumnos: [], filtered: true } })

    expect(wrapper.find('.students-empty-state').text()).toContain('No encontramos alumnos')
  })

  it('diferencia una base vacía de un filtro sin coincidencias', () => {
    const wrapper = mount(AlumnoList, { props: { alumnos: [] } })

    expect(wrapper.find('.students-empty-state').text()).toContain('Todavía no hay alumnos')
  })
})
