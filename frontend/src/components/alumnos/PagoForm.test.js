import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import PagoForm from './PagoForm.vue'

const createPago = vi.hoisted(() => vi.fn().mockResolvedValue({ id: 9 }))
const loadPagos = vi.hoisted(() => vi.fn().mockResolvedValue(undefined))
const getEstadoCuenta = vi.hoisted(() => vi.fn().mockResolvedValue({
  resumen: { saldo_pendiente: '50000.00', saldo_a_favor: '0.00' },
  cuotas: [
    { id: 1, concepto_nombre: 'Cuota', periodo: '01-2027', fecha_vencimiento: '2027-01-10', saldo: '25000.00', estado: 'pendiente' },
    { id: 2, concepto_nombre: 'Cuota', periodo: '02-2027', fecha_vencimiento: '2027-02-10', saldo: '25000.00', estado: 'pendiente' },
  ],
}))
const confirmSaldoAFavor = vi.hoisted(() => vi.fn().mockResolvedValue({ isConfirmed: true }))
const toastError = vi.hoisted(() => vi.fn())
const getRecibo = vi.hoisted(() => vi.fn())

vi.mock('@/composables/usePagos', () => ({
  usePagos: () => ({ createPago, loadPagos, getEstadoCuenta, getRecibo }),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: vi.fn(), error: toastError }),
}))

vi.mock('@/lib/swal', () => ({ confirmSaldoAFavor }))

const alumno = { id: 12, nombre: 'Ana', apellido: 'López' }

async function mountForm() {
  const wrapper = mount(PagoForm, {
    props: { open: true, alumno },
    global: { stubs: { Teleport: true } },
  })
  await flushPromises()
  return wrapper
}

describe('PagoForm', () => {
  beforeEach(() => vi.clearAllMocks())

  it('recupera un error de carga inicial sin permitir un pago a ciegas', async () => {
    getEstadoCuenta.mockRejectedValueOnce(new Error('Cuotas no disponibles'))
    const wrapper = await mountForm()
    expect(wrapper.text()).toContain('Cuotas no disponibles')
    expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()
    await wrapper.findAll('button').find(button => button.text() === 'Reintentar cuotas').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('50.000')
    expect(createPago).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('conserva la confirmación, emite saved una sola vez y no vuelve a cobrar al fallar el recibo', async () => {
    createPago.mockResolvedValueOnce({ id: 9, alumno_nombre: 'López, Ana', importe: '30000', medio: 'efectivo', numero_recibo: 'REC-9' })
    getRecibo.mockRejectedValueOnce(new Error('Lectura fallida')).mockResolvedValueOnce({ numero: 'REC-9', pago: { importe: '30000' }, aplicaciones: [] })
    const wrapper = await mountForm()
    await wrapper.get('input[type="number"]').setValue('30000')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('Pago registrado')
    expect(wrapper.text()).toContain('REC-9')
    expect(wrapper.emitted('saved')).toEqual([[expect.objectContaining({ id: 9 })]])
    expect(wrapper.emitted('close')).toBeUndefined()
    expect(loadPagos).not.toHaveBeenCalled()
    await wrapper.get('form').trigger('submit')
    await wrapper.findAll('button').find(button => button.text() === 'Ver recibo').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Lectura fallida')
    await wrapper.findAll('button').find(button => button.text() === 'Reintentar recibo').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Recibo N.º REC-9')
    expect(createPago).toHaveBeenCalledTimes(1)
    await wrapper.setProps({ alumno: null, refreshError: 'Lista no disponible' })
    expect(wrapper.text()).toContain('Lista no disponible')
    expect(wrapper.text()).toContain('Pago registrado')
    wrapper.unmount()
  })

  it('bloquea doble envío mientras el registro está pendiente', async () => {
    let finish
    createPago.mockImplementationOnce(() => new Promise(resolve => { finish = resolve }))
    const wrapper = await mountForm()
    await wrapper.get('input[type="number"]').setValue('30000')
    await wrapper.get('form').trigger('submit')
    await wrapper.get('form').trigger('submit')
    expect(createPago).toHaveBeenCalledTimes(1)
    finish({ id: 10, importe: '30000', medio: 'efectivo' })
    await flushPromises()
    wrapper.unmount()
  })

  it('muestra la deuda y aplica automáticamente a las cuotas más antiguas', async () => {
    const wrapper = await mountForm()

    expect(wrapper.text()).toContain('Deuda pendiente')
    expect(wrapper.text()).toContain('$ 50.000')
    await wrapper.get('input[type="number"]').setValue('30000')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createPago).toHaveBeenCalledWith(expect.objectContaining({
      alumno: 12,
      cuotas: [],
      aplicacion_automatica: true,
      importe: 30000,
    }))
    expect(confirmSaldoAFavor).not.toHaveBeenCalled()
  })

  it('permite elegir varias cuotas y confirma solamente el excedente', async () => {
    const wrapper = await mountForm()
    await wrapper.get('input[type="radio"][value="manual"]').setValue()
    const checks = wrapper.findAll('input[type="checkbox"]')
    await checks[1].setValue(true)
    await wrapper.get('input[type="number"]').setValue('30000')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(confirmSaldoAFavor).toHaveBeenCalledWith({
      importe: 30000,
      saldo: 25000,
      importeAplicado: 25000,
      saldoFavor: 5000,
    })
    expect(createPago).toHaveBeenCalledWith(expect.objectContaining({
      cuotas: [2],
      aplicacion_automatica: false,
    }))
  })
})
