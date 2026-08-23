import { flushPromises, shallowMount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import AlumnoDetail from '@/components/alumnos/AlumnoDetail.vue'
import ImportacionesView from './ImportacionesView.vue'

vi.mock('@/lib/api', () => ({
  apiRequest: vi.fn(async () => []),
  downloadFile: vi.fn(),
  uploadFile: vi.fn(),
}))

vi.mock('@/lib/swal', () => ({ confirmImportacion: vi.fn() }))

describe('textos operativos aclaratorios', () => {
  it('explica que los conceptos facturables no son una matrícula', () => {
    const wrapper = shallowMount(AlumnoDetail, {
      props: {
        alumno: { id: 1, nombre: 'Ana', apellido: 'Pérez', sucursal: 1, estado: 'activo' },
        conceptos: [],
      },
    })

    expect(wrapper.text()).toContain('Conceptos facturables')
    expect(wrapper.text()).toContain('Son conceptos activos de la sucursal; no representan una matrícula vigente')
  })

  it('presenta las columnas de importación en lenguaje administrativo', async () => {
    const wrapper = shallowMount(ImportacionesView)
    await flushPromises()

    expect(wrapper.get('.imports-hint').text()).toContain('completá apellido, nombre, DNI y código de sucursal')
    expect(wrapper.get('.imports-hint').text()).not.toContain('sucursal_codigo')
    expect(wrapper.get('.imports-hint').text()).not.toContain('`')
  })
})
