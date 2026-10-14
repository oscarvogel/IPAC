import { mount, flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import OperacionDetalle from './OperacionDetalle.vue'
const getRecibo = vi.hoisted(() => vi.fn())
vi.mock('@/composables/usePagos', () => ({ usePagos: () => ({ getRecibo }) }))
describe('detalle de operación', () => {

  it('test_muestra_comprobante_origen_destino_y_ejecutor', () => {
    const cajaOrigen = { id: 11, sucursal: 1, sucursal_nombre: 'Posadas', usuario: 4, usuario_nombre: 'cajera-origen' }
    const cajaDestino = { id: 22, sucursal: 2, sucursal_nombre: 'Eldorado', usuario: 5, usuario_nombre: 'cajero-destino' }
    for (const [tipo, caja, sentido, contraparte] of [
      ['pase', 11, 'salida', cajaDestino],
      ['ingreso', 22, 'entrada', cajaOrigen],
    ]) {
      const wrapper = mount(OperacionDetalle, {
        props: { operacion: {
          id: 100, caja, tipo, tipo_label: tipo === 'pase' ? 'Pase' : 'Ingreso',
          importe: '30.00', medio: 'efectivo', descripcion: 'Refuerzo de efectivo',
          transferencia: {
            id: 7, numero_comprobante: 'TRF-00000007', sentido,
            contraparte, motivo: 'Refuerzo de efectivo',
            actor: { id: 9, username: 'admin-ejecutor', nombre: 'Ana Administración' },
          },
        } },
        global: { stubs: { Teleport: true } },
      })
      const fields = Object.fromEntries(wrapper.findAll('dl > div').map(field => [
        field.get('dt').text(), field.get('dd').text(),
      ]))
      expect(fields['Referencia']).toBe('TRF-00000007')
      expect(fields[tipo === 'pase' ? 'Caja de destino' : 'Caja de origen']).toBe('Caja ' + contraparte.id)
      expect(fields['Sucursal contraparte']).toBe(contraparte.sucursal_nombre)
      expect(fields['Cajero contraparte']).toBe(contraparte.usuario_nombre)
      expect(fields['Motivo de transferencia']).toBe('Refuerzo de efectivo')
      expect(fields['Ejecutado por']).toBe('Ana Administración (admin-ejecutor)')
      expect(fields['Tipo']).toBe(tipo === 'pase' ? 'Pase' : 'Ingreso')
      expect(wrapper.findAll('button').some(button => button.text() === 'Ver recibo')).toBe(false)
      wrapper.unmount()
    }
  })

  it('muestra otra caja cuando la contraparte está fuera del alcance', () => {
    const wrapper = mount(OperacionDetalle, {
      props: { operacion: {
        id: 100, tipo: 'ingreso', tipo_label: 'Ingreso', importe: '30.00', medio: 'efectivo',
        transferencia: {
          id: 7, numero_comprobante: 'TRF-00000007', sentido: 'entrada', contraparte: null,
          motivo: 'Refuerzo de efectivo', actor: { id: 9, username: 'admin-ejecutor', nombre: '' },
        },
      } }, global: { stubs: { Teleport: true } },
    })
    const fields = Object.fromEntries(wrapper.findAll('dl > div').map(field => [
      field.get('dt').text(), field.get('dd').text(),
    ]))
    expect(fields['Referencia']).toBe('TRF-00000007')
    expect(fields['Caja de origen']).toBe('Otra caja')
    expect(fields['Ejecutado por']).toBe('admin-ejecutor')
    expect(fields).not.toHaveProperty('Sucursal contraparte')
    expect(fields).not.toHaveProperty('Cajero contraparte')
    wrapper.unmount()
  })

  it('test_movimiento_sin_transferencia_conserva_detalle_actual', () => {
    const wrapper = mount(OperacionDetalle, {
      props: { operacion: {
        id: 1, tipo: 'pago', tipo_label: 'Pago', pago: 5, pago_numero_recibo: 'REC-5',
        importe: '200', medio: 'efectivo', descripcion: 'Cuota mensual',
        usuario_nombre: 'Cajero QA', transferencia: null,
      } },
      global: { stubs: { Teleport: true } },
    })
    const fields = Object.fromEntries(wrapper.findAll('dl > div').map(field => [
      field.get('dt').text(), field.get('dd').text(),
    ]))
    expect(fields['Referencia']).toBe('REC-5')
    expect(fields['Descripción']).toBe('Cuota mensual')
    expect(fields['Cajero']).toBe('Cajero QA')
    expect(wrapper.findAll('button').some(button => button.text() === 'Ver recibo')).toBe(true)
    for (const label of ['Caja de origen', 'Caja de destino', 'Sucursal contraparte', 'Cajero contraparte', 'Motivo de transferencia', 'Ejecutado por']) {
      expect(fields).not.toHaveProperty(label)
    }
    wrapper.unmount()
  })
  it('navega al recibo con un único diálogo y reintenta solo la lectura', async () => {
    getRecibo.mockRejectedValueOnce(new Error('No se pudo leer')).mockResolvedValueOnce({ numero: 'REC-5', pago: { importe: '200' }, aplicaciones: [] })
    const previousFocus = document.createElement('button')
    document.body.append(previousFocus)
    previousFocus.focus()
    const wrapper = mount(OperacionDetalle, { props: { operacion: { id: 1, pago: 5, tipo_label: 'Pago', importe: '200', medio: 'efectivo', usuario_nombre: 'Cajero QA' } }, global: { stubs: { Teleport: true } }, attachTo: document.body })
    await wrapper.findAll('button').find(button => button.text() === 'Ver recibo').trigger('click'); await flushPromises()
    expect(wrapper.text()).toContain('No se pudo leer')
    await wrapper.findAll('button').find(button => button.text() === 'Reintentar recibo').trigger('click'); await flushPromises()
    expect(wrapper.text()).toContain('REC-5')
    expect(wrapper.findAll('[role="dialog"]')).toHaveLength(1)
    await wrapper.findAll('button').find(button => button.text() === 'Volver al detalle').trigger('click')
    expect(wrapper.text()).toContain('Cajero QA')
    await wrapper.get('[role="dialog"]').trigger('keydown', { key: 'Escape' })
    expect(wrapper.emitted('close')).toHaveLength(1)
    wrapper.unmount()
    await new Promise((resolve) => requestAnimationFrame(resolve))
    expect(document.activeElement).toBe(previousFocus)
    previousFocus.remove()
  })
})
