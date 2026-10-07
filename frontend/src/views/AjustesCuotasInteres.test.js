import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import AjustesCuotasView from '@/views/AjustesCuotasView.vue'

const apiRequest = vi.hoisted(() => vi.fn())
const toast = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }))

vi.mock('@/lib/api', () => ({
  apiRequest,
  downloadFile: vi.fn(),
  uploadFile: vi.fn(),
}))

vi.mock('@/composables/useCatalogos', () => ({
  useCatalogos: () => ({
    sucursales: ref([{ id: 1, nombre: 'Posadas' }, { id: 2, nombre: 'Eldorado' }]),
    conceptos: ref([]),
    loadCatalogo: vi.fn().mockResolvedValue(undefined),
    loadCatalogos: vi.fn().mockResolvedValue(undefined),
  }),
}))

vi.mock('@/composables/useToast', () => ({ useToast: () => toast }))

vi.mock('@/components/ui/AppPageState.vue', () => ({
  default: { props: ['loading', 'error', 'label'], template: '<div />' },
}))

const global = { stubs: { RouterLink: true } }

// El separador entre el signo y el número depende del runtime (en Node sale
// `$ 1.650,00`, en el navegador puede ser espacio fino). Se usa el mismo
// formateador que la vista para no depender de eso.
function ars(valor) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(valor)
}

function responder(rutas) {
  apiRequest.mockImplementation(async (path, options) => {
    // Se elige el prefijo MÁS largo: '/tasas-interes/' matchea también
    // '/tasas-interes/proyectar/' y el mock devolvería el listado donde va la
    // proyección.
    const clave = Object.keys(rutas)
      .filter((prefijo) => String(path).startsWith(prefijo))
      .sort((a, b) => b.length - a.length)[0]
    const valor = clave ? rutas[clave] : null
    return typeof valor === 'function' ? valor(options) : valor
  })
}

async function montar() {
  const wrapper = mount(AjustesCuotasView, { global })
  await flushPromises()
  return wrapper
}

describe('ajustes de cuotas: interés de mora', () => {
  beforeEach(() => {
    apiRequest.mockReset()
    toast.success.mockReset()
    toast.error.mockReset()
  })

  it('carga las tasas de interés junto con los descuentos y recargos', async () => {
    responder({
      '/tipos-descuento/': { results: [] },
      '/reglas-recargo/': { results: [] },
      '/tasas-interes/': {
        results: [{
          id: 7,
          sucursal: 1,
          sucursal_nombre: 'Posadas',
          porcentaje_mensual: '5.500',
          vigencia_desde: '2026-01-01',
          vigencia_hasta: null,
          base_calculo: 'dia_1_del_mes',
          unidad_calculo: 'meses',
          activa: true,
        }],
      },
    })

    const wrapper = await montar()

    const rutas = apiRequest.mock.calls.map(([path]) => path)
    expect(rutas).toContain('/tasas-interes/')
    expect(wrapper.text()).toContain('5,5% mensual')
    expect(wrapper.text()).toContain('desde el día 1 del mes')
  })

  it('traduce la base y la unidad a texto legible', async () => {
    responder({
      '/tipos-descuento/': { results: [] },
      '/reglas-recargo/': { results: [] },
      '/tasas-interes/': {
        results: [{
          id: 8,
          sucursal: 2,
          sucursal_nombre: 'Eldorado',
          porcentaje_mensual: '9.000',
          vigencia_desde: '2026-04-01',
          vigencia_hasta: '2026-06-30',
          base_calculo: 'fecha_vencimiento',
          unidad_calculo: 'dias',
          activa: true,
        }],
      },
    })

    const wrapper = await montar()

    expect(wrapper.text()).toContain('desde el vencimiento')
    expect(wrapper.text()).toContain('días prorrateados')
    expect(wrapper.text()).toContain('01/04/2026')
    expect(wrapper.text()).toContain('30/06/2026')
  })

  it('manda la vigencia hasta vacía como null y no como cadena', async () => {
    responder({
      '/tipos-descuento/': { results: [] },
      '/reglas-recargo/': { results: [] },
      '/tasas-interes/': { results: [] },
    })
    const wrapper = await montar()

    await wrapper.find('section.adjustment-card--wide form button[type="submit"]').trigger('submit')
    await flushPromises()

    const llamada = apiRequest.mock.calls.find(([path, options]) => path === '/tasas-interes/' && options?.method === 'POST')
    expect(llamada).toBeDefined()
    // Sin esto el backend recibe "" y Django lo rechaza como fecha inválida.
    expect(llamada[1].body.vigencia_hasta).toBeNull()
  })

  it('proyecta el interés a la fecha elegida y muestra el total', async () => {
    responder({
      '/tipos-descuento/': { results: [] },
      '/reglas-recargo/': { results: [] },
      '/tasas-interes/': { results: [] },
      '/tasas-interes/proyectar/': {
        fecha_evaluacion: '2026-04-01',
        cuotas_evaluadas: 3,
        cuotas_con_interes: 2,
        total_interes: '1650.00',
        sin_tasa: [],
        detalle: [
          { cuota_id: 11, sucursal_id: 1, saldo_pendiente: '10000.00', dias_interesables: 31, periodos: '1.00', importe: '550.00' },
          { cuota_id: 12, sucursal_id: 1, saldo_pendiente: '20000.00', dias_interesables: 31, periodos: '1.00', importe: '1100.00' },
        ],
      },
    })
    const wrapper = await montar()

    await wrapper.find('.projection-controls button').trigger('click')
    await flushPromises()

    const llamada = apiRequest.mock.calls.find(([path]) => String(path).startsWith('/tasas-interes/proyectar/'))
    // Sin `method` y sin `body`: es un GET. Si alguna vez se mandara por POST caería
    // en write_roles y el rol caja no podría ver el interés que le toca cobrar.
    expect(llamada[1].method).toBeUndefined()
    expect(llamada[1].body).toBeUndefined()
    expect(llamada[1].query).toEqual({ fecha_evaluacion: expect.any(String) })
    expect(wrapper.text()).toContain(ars(1650))
    expect(wrapper.findAll('.projection-table tbody tr')).toHaveLength(2)
  })

  it('avisa cuando hay cuotas de una sucursal sin tasa cargada', async () => {
    responder({
      '/tipos-descuento/': { results: [] },
      '/reglas-recargo/': { results: [] },
      '/tasas-interes/': { results: [] },
      '/tasas-interes/proyectar/': {
        fecha_evaluacion: '2026-04-01',
        cuotas_evaluadas: 2,
        cuotas_con_interes: 1,
        total_interes: '550.00',
        sin_tasa: [42],
        detalle: [
          { cuota_id: 11, sucursal_id: 1, saldo_pendiente: '10000.00', dias_interesables: 31, periodos: '1.00', importe: '550.00' },
        ],
      },
    })
    const wrapper = await montar()

    await wrapper.find('.projection-controls button').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('1 cuota quedó afuera')
    expect(wrapper.text()).not.toContain('1 cuotas quedaron')
  })

  it('usa el plural cuando son varias las cuotas sin tasa', async () => {
    responder({
      '/tipos-descuento/': { results: [] },
      '/reglas-recargo/': { results: [] },
      '/tasas-interes/': { results: [] },
      '/tasas-interes/proyectar/': {
        fecha_evaluacion: '2026-04-01',
        cuotas_evaluadas: 5,
        cuotas_con_interes: 1,
        total_interes: '550.00',
        sin_tasa: [42, 43, 44],
        detalle: [
          { cuota_id: 11, sucursal_id: 1, saldo_pendiente: '10000.00', dias_interesables: 31, periodos: '1.00', importe: '550.00' },
        ],
      },
    })
    const wrapper = await montar()

    await wrapper.find('.projection-controls button').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('3 cuotas quedaron afuera')
  })

  it('muestra en línea el motivo cuando no hay ninguna tasa cargada', async () => {
    responder({
      '/tipos-descuento/': { results: [] },
      '/reglas-recargo/': { results: [] },
      '/tasas-interes/': { results: [] },
      '/tasas-interes/proyectar/': () => {
        throw new Error('No hay ninguna tasa de interés cargada para el alcance consultado. Cargá una tasa con vigencia antes de calcular el interés de las cuotas.')
      },
    })
    const wrapper = await montar()

    await wrapper.find('.projection-controls button').trigger('click')
    await flushPromises()

    const mensaje = wrapper.find('.projection-message.is-error')
    expect(mensaje.exists()).toBe(true)
    expect(mensaje.text()).toContain('No hay ninguna tasa de interés cargada')
  })

  it('dice que no hay cuotas con saldo en lugar de una tabla vacía', async () => {
    responder({
      '/tipos-descuento/': { results: [] },
      '/reglas-recargo/': { results: [] },
      '/tasas-interes/': { results: [] },
      '/tasas-interes/proyectar/': {
        fecha_evaluacion: '2026-04-01',
        cuotas_evaluadas: 0,
        cuotas_con_interes: 0,
        total_interes: '0.00',
        sin_tasa: [],
        detalle: [],
      },
    })
    const wrapper = await montar()

    await wrapper.find('.projection-controls button').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('No hay cuotas con saldo para esa fecha')
    expect(wrapper.find('.projection-table').exists()).toBe(false)
  })

  it('desactiva una tasa con PATCH y recarga el listado', async () => {
    responder({
      '/tipos-descuento/': { results: [] },
      '/reglas-recargo/': { results: [] },
      '/tasas-interes/7/': {},
      '/tasas-interes/': {
        results: [{
          id: 7,
          sucursal: 1,
          sucursal_nombre: 'Posadas',
          porcentaje_mensual: '5.500',
          vigencia_desde: '2026-01-01',
          vigencia_hasta: null,
          base_calculo: 'dia_1_del_mes',
          unidad_calculo: 'meses',
          activa: true,
        }],
      },
    })
    const wrapper = await montar()

    await wrapper.find('.adjustment-card--wide .adjustment-list button').trigger('click')
    await flushPromises()

    const llamada = apiRequest.mock.calls.find(([path]) => path === '/tasas-interes/7/')
    expect(llamada[1]).toEqual({ method: 'PATCH', body: { activa: false } })
  })
})