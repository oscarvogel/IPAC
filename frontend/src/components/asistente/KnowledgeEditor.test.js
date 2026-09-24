import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import KnowledgeEditor from './KnowledgeEditor.vue'

const emptyArticle = {
  clave: '',
  titulo: '',
  modulo: 'alumnos',
  preguntas_equivalentes: [],
  descripcion: '',
  pasos: [],
  ruta: '',
  action_label: '',
  roles_permitidos: [],
  notas: [],
  activo: true,
  orden: 0,
}

describe('KnowledgeEditor', () => {
  it('agrega preguntas equivalentes desde la interfaz', async () => {
    const wrapper = mount(KnowledgeEditor, {
      props: { modelValue: emptyArticle },
    })

    await wrapper.get('[data-testid="add-alias"]').trigger('click')

    expect(wrapper.findAll('[data-testid="alias-input"]')).toHaveLength(1)
  })

  it('emite un artículo estructurado al guardar', async () => {
    const wrapper = mount(KnowledgeEditor, {
      props: {
        modelValue: {
          ...emptyArticle,
          clave: 'refinanciar_cuotas',
          titulo: 'Refinanciar cuotas',
          modulo: 'cobranzas',
          preguntas_equivalentes: ['como refinancio'],
          pasos: ['Abrí el estado de cuenta.'],
          roles_permitidos: ['administracion'],
        },
      },
    })

    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('save')[0][0]).toMatchObject({
      clave: 'refinanciar_cuotas',
      titulo: 'Refinanciar cuotas',
      modulo: 'cobranzas',
      preguntas_equivalentes: ['como refinancio'],
      pasos: ['Abrí el estado de cuenta.'],
      roles_permitidos: ['administracion'],
    })
  })
})
