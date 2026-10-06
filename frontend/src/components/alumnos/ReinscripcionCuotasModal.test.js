import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ReinscripcionCuotasModal from './ReinscripcionCuotasModal.vue'

const cargarPlanCuotas = vi.hoisted(() => vi.fn())
const generarCuotasDeMatricula = vi.hoisted(() => vi.fn())
const evaluar = vi.hoisted(() => vi.fn())
const confirmReinscripcionCuotas = vi.hoisted(() => vi.fn())
const toastSuccess = vi.hoisted(() => vi.fn())
const toastWarning = vi.hoisted(() => vi.fn())

const previsualizacion = {
  periodos: ref([]),
  etiquetasPeriodo: ref([]),
  cuotasAGenerar: ref(0),
  loading: ref(false),
  error: ref(''),
}

vi.mock('@/composables/useMatriculas', () => ({
  useMatriculas: () => ({ cargarPlanCuotas, generarCuotasDeMatricula }),
}))

vi.mock('@/composables/useCuotasMasivas', () => ({
  useCuotasMasivas: () => ({ ...previsualizacion, evaluar }),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: toastSuccess, warning: toastWarning, error: vi.fn() }),
}))

vi.mock('@/lib/swal', () => ({ confirmReinscripcionCuotas }))

const PLAN_CON_PLAN = {
  matricula: 3,
  alumno: 12,
  carrera: 7,
  carrera_nombre: 'Técnicatura en Sistemas',
  plan_cuotas: 10,
  fecha_inicio: '2026-03-01',
  periodos: [
    '2026-03', '2026-04', '2026-05', '2026-06', '2026-07',
    '2026-08', '2026-09', '2026-10', '2026-11', '2026-12',
  ],
  etiquetas_periodo: ['marzo 2026 (vence el 10)'],
  motivo_sin_plan: '',
  conceptos: [{ id: 5, nombre: 'Cuota mensual', importe: 82000 }],
}

const PLAN_SIN_PLAN = {
  ...PLAN_CON_PLAN,
  plan_cuotas: null,
  periodos: [],
  motivo_sin_plan: 'La carrera no tiene un plan de cuotas configurado. Indicá cuántas se generan.',
}

function montar(plan = PLAN_CON_PLAN, matricula = {}) {
  cargarPlanCuotas.mockResolvedValue(plan)
  return mount(ReinscripcionCuotasModal, {
    props: {
      open: true,
      alumno: { id: 12, nombre: 'Ana', apellido: 'López' },
      matricula: { id: 3, sucursal: 1, carrera: 7, estado: 'activa', fecha_inicio: '2026-03-01', ...matricula },
    },
    global: { stubs: { Teleport: true } },
  })
}

/** Deja el estado de la previsualizacion como lo devuelve el backend. */
function preview({ periodos: ps = [], etiquetas = [], aGenerar = 0 } = {}) {
  previsualizacion.periodos.value = ps
  previsualizacion.etiquetasPeriodo.value = etiquetas.length ? etiquetas : ps
  previsualizacion.cuotasAGenerar.value = aGenerar
}

describe('ReinscripcionCuotasModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    previsualizacion.periodos.value = []
    previsualizacion.etiquetasPeriodo.value = []
    previsualizacion.cuotasAGenerar.value = 0
    previsualizacion.loading.value = false
    previsualizacion.error.value = ''
    confirmReinscripcionCuotas.mockResolvedValue({ isConfirmed: true })
    generarCuotasDeMatricula.mockResolvedValue({ resumen: { creadas: 10, omitidas: 0 } })
  })

  it('prellena la cantidad con el plan de la carrera', async () => {
    const wrapper = montar()
    await flushPromises()

    expect(cargarPlanCuotas).toHaveBeenCalledWith(3)
    expect(wrapper.get('input[type="number"]').element.value).toBe('10')
    expect(wrapper.get('.reinscripcion-carrera input').element.value).toBe('Técnicatura en Sistemas')
  })

  it('arranca en el mes de la fecha de inicio de la matrícula', async () => {
    const wrapper = montar()
    await flushPromises()

    expect(wrapper.get('.reinscripcion-mes-inicial input').element.value).toBe('Marzo 2026')
  })

  it('previsualiza los periodos de ese alumno y no del grupo entero', async () => {
    await flushPromises()
    const wrapper = montar()
    await flushPromises()

    expect(evaluar).toHaveBeenCalledWith({
      sucursal: 1,
      carrera: 7,
      concepto: 5,
      alumno: 12,
      plan: { cantidad: 10, mes_inicial: 3, anio_inicial: 2026, dia_vencimiento: 10 },
    })
  })

  it('avisa cuántas ya existen y cuántas se van a generar', async () => {
    previsualizacion.periodos.value = PLAN_CON_PLAN.periodos
    previsualizacion.cuotasAGenerar.value = 7
    const wrapper = montar()
    await flushPromises()

    expect(wrapper.text()).toContain('3 ya existen')
    expect(wrapper.text()).toContain('7')
  })

  it('explica por qué hay que escribir la cantidad si la carrera no tiene plan', async () => {
    const wrapper = montar(PLAN_SIN_PLAN)
    await flushPromises()

    expect(wrapper.text()).toContain('no tiene un plan de cuotas configurado')
  })

  it('sin plan no deja la cantidad inventada: pide que la escriban', async () => {
    const wrapper = montar(PLAN_SIN_PLAN)
    await flushPromises()

    expect(wrapper.get('input[type="number"]').element.value).toBe('')
    expect(wrapper.text()).not.toContain('Calculando los períodos del lote.')
    expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()
    expect(evaluar).not.toHaveBeenCalled()
  })

  it('sin plan, la cantidad que escribe el operador recalcula los períodos', async () => {
    const wrapper = montar(PLAN_SIN_PLAN)
    await flushPromises()

    await wrapper.get('input[type="number"]').setValue(3)
    await flushPromises()

    expect(evaluar).toHaveBeenCalledWith({
      sucursal: 1,
      carrera: 7,
      concepto: 5,
      alumno: 12,
      plan: { cantidad: 3, mes_inicial: 3, anio_inicial: 2026, dia_vencimiento: 10 },
    })
  })

  it('sin plan muestra los períodos calculados y habilita el envío', async () => {
    preview({ periodos: ['2026-03', '2026-04', '2026-05'], aGenerar: 3 })
    const wrapper = montar(PLAN_SIN_PLAN)
    await flushPromises()
    await wrapper.get('input[type="number"]').setValue(3)
    await flushPromises()

    expect(wrapper.findAll('.reinscripcion-periodos li')).toHaveLength(3)
    expect(wrapper.text()).toContain('Se generan')
    expect(wrapper.text()).toContain('3')
    expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeUndefined()
  })

  it('bloquea el envío mientras la previsualización está en curso', async () => {
    previsualizacion.periodos.value = PLAN_CON_PLAN.periodos
    previsualizacion.cuotasAGenerar.value = 10
    previsualizacion.loading.value = true
    const wrapper = montar()
    await flushPromises()

    expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()
  })

  it('bloquea el envío si la previsualización falla', async () => {
    const wrapper = montar()
    await flushPromises()
    previsualizacion.error.value = 'El día de vencimiento debe estar entre 1 y 28.'
    await flushPromises()

    expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(confirmReinscripcionCuotas).not.toHaveBeenCalled()
  })

  it('no deja confirmar cuando el preview no produjo períodos', async () => {
    const wrapper = montar()
    await flushPromises()

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(confirmReinscripcionCuotas).not.toHaveBeenCalled()
    expect(generarCuotasDeMatricula).not.toHaveBeenCalled()
  })

  it('sin plan, la confirmación dice cuántas cuotas se van a generar', async () => {
    preview({ periodos: ['2026-03', '2026-04', '2026-05'], aGenerar: 3 })
    const wrapper = montar(PLAN_SIN_PLAN)
    await flushPromises()

    await wrapper.get('input[type="number"]').setValue(3)
    await flushPromises()
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(confirmReinscripcionCuotas).toHaveBeenCalledWith(
      expect.objectContaining({ cantidad: 3, periodos: '2026-03 a 2026-05 (3)' }),
    )
    expect(generarCuotasDeMatricula).toHaveBeenCalledWith(3, expect.objectContaining({ cantidad: 3 }))
  })

  it('bloquea el envío si la carrera no tiene concepto de cuota', async () => {
    const wrapper = montar({ ...PLAN_CON_PLAN, conceptos: [] })
    await flushPromises()

    expect(wrapper.text()).toContain('no tiene un concepto de cuota cargado')
    expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()
  })

  it('genera contra la matrícula, no contra el endpoint masivo', async () => {
    preview({ periodos: PLAN_CON_PLAN.periodos, aGenerar: 10 })
    const wrapper = montar()
    await flushPromises()

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(generarCuotasDeMatricula).toHaveBeenCalledWith(3, {
      concepto: 5,
      cantidad: 10,
      dia_vencimiento: 10,
      fecha_emision: expect.any(String),
    })
    expect(wrapper.emitted('saved')).toBeTruthy()
  })

  it('si el alumno ya tenía todo, lo dice y no promete que generó', async () => {
    generarCuotasDeMatricula.mockResolvedValue({ resumen: { creadas: 0, omitidas: 10 } })
    // El preview devuelve los periodos del lote aunque no haya nada que
    // generar: lo que ya existe se saltea, y eso sigue siendo una operacion
    // valida que el operador puede querer confirmar.
    preview({ periodos: PLAN_CON_PLAN.periodos, aGenerar: 0 })
    const wrapper = montar()
    await flushPromises()

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(toastWarning).toHaveBeenCalled()
    expect(toastSuccess).not.toHaveBeenCalled()
  })

  it('no genera nada si el operador cancela la confirmación', async () => {
    confirmReinscripcionCuotas.mockResolvedValue({ isConfirmed: false })
    const wrapper = montar()
    await flushPromises()

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(generarCuotasDeMatricula).not.toHaveBeenCalled()
  })
})
