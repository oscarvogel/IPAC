import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import TransferenciasCajaView from './TransferenciasCajaView.vue'
import { apiRequest } from '@/lib/api'
import { nextTick } from 'vue'

vi.mock('@/lib/api', () => ({ apiRequest: vi.fn() }))

const cajas = [
  { id: 11, fecha: '2026-10-13', sucursal: 1, sucursal_nombre: 'Posadas', usuario: 21, usuario_nombre: 'cajera.posadas', total_esperado: '1500.00' },
  { id: 12, fecha: '2026-10-13', sucursal: 2, sucursal_nombre: 'Eldorado', usuario: 22, usuario_nombre: 'cajero.eldorado', total_esperado: '200.00' },
]
const evidencia = {
  id: 31, numero_comprobante: 'TC-000031', creado: '2026-10-13T15:30:00-03:00',
  actor: { id: 7, username: 'administracion', nombre: 'Administración' },
  origen: cajas[0], destino: cajas[1], importe: '250.50', motivo: 'Reposición de efectivo',
  movimiento_origen_id: 51, movimiento_destino_id: 52,
}
let wrapper
let historial
let comandos

beforeEach(() => {
  historial = []
  comandos = []
  apiRequest.mockReset()
  apiRequest.mockImplementation(async (path, options = {}) => {
    if (path === '/transferencias-caja/cajas-abiertas/') return cajas
    if (path === '/transferencias-caja/' && options.method === 'POST') {
      comandos.push(options.body)
      historial = [evidencia]
      return evidencia
    }
    if (path === '/transferencias-caja/') return historial
    throw new Error('Consulta inesperada: ' + path)
  })
})

afterEach(() => {
  wrapper?.unmount()
  document.body.innerHTML = ''
})

async function openView() {
  wrapper = mount(TransferenciasCajaView, { attachTo: document.body })
  await flushPromises()
  return wrapper
}

async function completeForm() {
  await wrapper.get('#transferencia-origen').setValue('11')
  await wrapper.get('#transferencia-destino').setValue('12')
  await wrapper.get('#transferencia-importe').setValue('250.50')
  await wrapper.get('#transferencia-motivo').setValue('Reposición de efectivo')
}

describe('Transferencias independientes de la caja propia', () => {
  it('test_admin_sin_caja_propia_puede_cargar_transferencias', async () => {
    await openView()
    expect(wrapper.get('h1').text()).toBe('Transferencias entre cajas')
    expect(wrapper.get('#transferencia-origen').text()).toContain('cajera.posadas')
    expect(wrapper.get('#transferencia-destino').text()).toContain('cajero.eldorado')
    expect(wrapper.text()).toContain('No hay transferencias recientes')
    expect(apiRequest.mock.calls.map(([path]) => path).sort()).toEqual([
      '/transferencias-caja/', '/transferencias-caja/cajas-abiertas/',
    ])
  })

  it('test_exige_origen_destino_importe_y_motivo', async () => {
    await openView()
    await wrapper.get('form').trigger('submit')
    expect(wrapper.find('[role="alertdialog"]').exists()).toBe(false)
    expect(wrapper.get('[role="alert"]').text()).toMatch(/origen.*destino.*importe.*motivo/i)
    expect(comandos).toEqual([])
    await completeForm()
    await wrapper.get('#transferencia-motivo').setValue('   ')
    await wrapper.get('form').trigger('submit')
    expect(wrapper.find('[role="alertdialog"]').exists()).toBe(false)
    expect(comandos).toEqual([])
  })

  it('test_no_permite_seleccionar_la_misma_caja', async () => {
    await openView()
    await wrapper.get('#transferencia-destino').setValue('11')
    await wrapper.get('#transferencia-origen').setValue('11')
    expect(wrapper.get('#transferencia-destino').element.value).toBe('')
    expect(wrapper.get('#transferencia-destino option[value="11"]').attributes('disabled')).toBeDefined()
    await wrapper.get('#transferencia-importe').setValue('250.50')
    await wrapper.get('#transferencia-motivo').setValue('Reposición')
    await wrapper.get('form').trigger('submit')
    expect(wrapper.find('[role="alertdialog"]').exists()).toBe(false)
    expect(comandos).toEqual([])
  })

  it('test_actualiza_historial_y_muestra_comprobante_al_confirmar', async () => {
    await openView()
    await completeForm()
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    const dialog = document.querySelector('[role="alertdialog"]')
    expect(dialog).not.toBeNull()
    expect(dialog.textContent).toContain('Posadas')
    expect(dialog.textContent).toContain('Eldorado')
    expect(dialog.textContent).toContain('250,50')
    expect(dialog.textContent).toContain('Reposición de efectivo')
    expect(comandos).toEqual([])
    const confirm = [...dialog.querySelectorAll('button')].find((button) => button.textContent.includes('Confirmar transferencia'))
    confirm.click()
    await flushPromises()
    expect(comandos).toEqual([{ origen_id: 11, destino_id: 12, importe: '250.50', motivo: 'Reposición de efectivo' }])
    expect(wrapper.get('[role="status"]').text()).toContain('TC-000031')
    const history = wrapper.get('[aria-labelledby="transferencias-historial-title"]')
    expect(history.text()).toContain('TC-000031')
    expect(history.text()).toContain('administracion')
    expect(history.text()).toContain('51')
    expect(history.text()).toContain('52')
    expect(document.querySelector('[role="alertdialog"]')).toBeNull()
  })
})

describe('Estados y recuperación de transferencias', () => {
  it('no envía motivos que exceden el contrato de 180 caracteres', async () => {
    await openView()
    await completeForm()
    await wrapper.get('#transferencia-motivo').setValue('a'.repeat(181))
    await wrapper.get('form').trigger('submit')
    expect(document.querySelector('[role="alertdialog"]')).toBeNull()
    expect(wrapper.get('[role="alert"]').text()).toContain('180')
    expect(comandos).toEqual([])
  })

  it('muestra carga y permite reintentar una consulta fallida', async () => {
    let fail
    apiRequest.mockImplementationOnce(() => new Promise((resolve, reject) => { fail = reject }))
    wrapper = mount(TransferenciasCajaView, { attachTo: document.body })
    await nextTick()
    expect(wrapper.get('[role="status"]').text()).toContain('Cargando')
    expect(wrapper.attributes('aria-busy')).toBe('true')
    fail(new Error('Sin conexión'))
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Sin conexión')
    const retry = wrapper.findAll('button').find((button) => button.text().includes('Reintentar'))
    await retry.trigger('click')
    await flushPromises()
    expect(wrapper.get('#transferencia-origen').text()).toContain('Posadas')
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
  })

  it('explica las cajas insuficientes y conserva historial de cajas cerradas', async () => {
    apiRequest.mockImplementation(async (path) => path.includes('cajas-abiertas') ? [] : [evidencia])
    await openView()
    expect(wrapper.text()).toContain('No hay cajas abiertas')
    expect(wrapper.find('form').exists()).toBe(false)
    expect(wrapper.get('[aria-labelledby="transferencias-historial-title"]').text()).toContain('TC-000031')
  })

  it('conserva el comprobante si falla la actualización después del POST', async () => {
    await openView()
    apiRequest.mockImplementation(async (path, options = {}) => {
      if (options.method === 'POST') { comandos.push(options.body); return evidencia }
      throw new Error('Sin conexión')
    })
    await completeForm()
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    const confirm = [...document.querySelectorAll('[role="alertdialog"] button')].find((button) => button.textContent.includes('Confirmar transferencia'))
    confirm.click()
    confirm.click()
    await flushPromises()
    expect(comandos).toHaveLength(1)
    expect(wrapper.get('[role="status"]').text()).toContain('TC-000031')
    expect(wrapper.get('[role="alert"]').text()).toContain('se registró')
    expect(wrapper.get('[aria-labelledby="transferencias-historial-title"]').text()).toContain('TC-000031')
  })

  it('muestra el rechazo de API y conserva datos para corregirlos', async () => {
    await openView()
    apiRequest.mockImplementation(async () => { throw new Error('Efectivo insuficiente') })
    await completeForm()
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    const confirm = [...document.querySelectorAll('[role="alertdialog"] button')].find((button) => button.textContent.includes('Confirmar transferencia'))
    confirm.click()
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Efectivo insuficiente')
    expect(wrapper.get('#transferencia-motivo').element.value).toBe('Reposición de efectivo')
    expect(document.querySelector('[role="alertdialog"]')).toBeNull()
  })
})
