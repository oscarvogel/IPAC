import { flushPromises, shallowMount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AlumnosView from './AlumnosView.vue'
import CajaView from './CajaView.vue'
import ReportesView from './ReportesView.vue'

const routeState = vi.hoisted(() => ({
  role: 'administracion',
  cashStatus: 'abierta',
  toastErrors: [],
  alumnosRef: null,
  selectedAlumnoRef: null,
  paginationRef: null,
}))

vi.mock('@/composables/useAuth', async () => {
  const { computed } = await import('vue')
  const capabilities = {
    administracion: ['manage-alumnos', 'manage-fees', 'operate-cash', 'register-payments'],
    consulta: [],
  }
  return {
    useAuth: () => ({
      user: computed(() => ({ username: 'admin', perfil: { rol: routeState.role, sucursal: { nombre: 'Posadas' } } })),
      can: (capability) => capabilities[routeState.role]?.includes(capability) || false,
    }),
  }
})

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: (message) => routeState.toastErrors.push(message),
  }),
}))

vi.mock('@/composables/useAlumnos', async () => {
  const { ref } = await import('vue')
  const alumnos = ref([])
  const selectedAlumno = ref(null)
  const pagination = ref({ count: 0, page: 1, pageSize: 10 })
  const alumnoStats = ref({ activos: 0, inactivos: 0 })
  routeState.alumnosRef = alumnos
  routeState.selectedAlumnoRef = selectedAlumno
  routeState.paginationRef = pagination
  return {
    useAlumnos: () => ({
      alumnos,
      selectedAlumno,
      pagination,
      alumnoStats,
      loading: ref(false),
      error: ref(''),
      setSelected: vi.fn((id) => {
        selectedAlumno.value = alumnos.value.find((alumno) => String(alumno.id) === String(id)) || null
      }),
      loadAlumnos: vi.fn(async (query) => {
        pagination.value.page = Number(query?.page || 1)
      }),
      loadAlumnoStats: vi.fn(async () => {}),
      deactivateAlumno: vi.fn(),
      reactivateAlumno: vi.fn(),
    }),
  }
})

vi.mock('@/composables/useCatalogos', async () => {
  const { ref } = await import('vue')
  return {
    useCatalogos: () => ({
      sucursales: ref([]),
      carreras: ref([]),
      conceptos: ref([]),
      loadCatalogos: vi.fn(async () => {}),
    }),
  }
})

vi.mock('@/composables/usePagos', async () => {
  const { ref } = await import('vue')
  return { usePagos: () => ({ pagos: ref([]), loadPagos: vi.fn(async () => {}) }) }
})

vi.mock('@/composables/useCaja', async () => {
  const { computed, ref } = await import('vue')
  return {
    useCaja: () => ({
      cajaHoy: computed(() => routeState.cashStatus
        ? { id: 1, estado: routeState.cashStatus, fecha: '2026-08-22', sucursal_nombre: 'Posadas' }
        : null),
      saldoAnterior: ref(null),
      cajaMovimientos: ref([]),
      cajaTotales: ref({
        saldoInicial: 0,
        cobranzasEfectivo: 0,
        efectivoEsperado: 0,
        saldoFinalFisico: 0,
        egresosEfectivo: 0,
        retirosEfectivo: 0,
        totalCobrado: 0,
        transferencia: 0,
        mercadoPago: 0,
        tarjeta: 0,
        otro: 0,
      }),
      loading: ref(false),
      error: ref(''),
      loadCajaHoy: vi.fn(async () => {}),
      createMovimiento: vi.fn(),
      cerrarCaja: vi.fn(),
      aplicarSaldoAnterior: vi.fn(),
    }),
  }
})

vi.mock('@/composables/useReportes', async () => {
  const { ref } = await import('vue')
  return {
    useReportes: () => ({
      resumen: ref({ cajas: {} }),
      pagos: ref([]),
      cobranzasUsuarios: ref([]),
      cajasHistorial: ref([]),
      cajasHistorialPaginacion: ref({ count: 0, page: 1, page_size: 10, next: null, previous: null }),
      cajasHistorialUsuarios: ref([]),
      loading: ref(false),
      error: ref(''),
      loadResumen: vi.fn(async () => {}),
      loadPagos: vi.fn(async () => {}),
      loadCobranzasUsuarios: vi.fn(async () => {}),
      loadCajasHistorial: vi.fn(async () => {}),
      loadCajaDetalle: vi.fn(async () => ({ movimientos: [] })),
      exportarExcel: vi.fn(),
    }),
  }
})

async function mountAt(component, path, stubs = {}, attachTo = null) {
  const routePath = path.split('?')[0]
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: routePath, component: { template: '<div />' } }],
  })
  await router.push(path)
  await router.isReady()
  const mountOptions = { global: { plugins: [router], stubs } }
  if (attachTo) mountOptions.attachTo = attachTo
  const wrapper = shallowMount(component, mountOptions)
  await flushPromises()
  return { wrapper, router }
}

describe('acciones profundas de Alumnos', () => {
  beforeEach(() => {
    routeState.role = 'administracion'
    if (routeState.alumnosRef) routeState.alumnosRef.value = []
    if (routeState.selectedAlumnoRef) routeState.selectedAlumnoRef.value = null
    if (routeState.paginationRef) routeState.paginationRef.value = { count: 0, page: 1, pageSize: 10 }
  })

  it('mantiene visible la búsqueda y su valor mientras se actualizan los filtros', async () => {
    const { wrapper } = await mountAt(AlumnosView, '/alumnos')
    const input = wrapper.get('input[type="search"]')

    await input.setValue('vo')
    await flushPromises()

    expect(wrapper.get('input[type="search"]').element.value).toBe('vo')
    expect(wrapper.get('input[type="search"]').isVisible()).toBe(true)
    expect(wrapper.text()).toContain('Búsqueda: vo')

    await input.setValue('')
    await flushPromises()

    expect(wrapper.get('input[type="search"]').element.value).toBe('')
    expect(wrapper.text()).not.toContain('Búsqueda: vo')
  })

  it('abre Nuevo alumno una vez y limpia accion de la URL', async () => {
    const { wrapper, router } = await mountAt(AlumnosView, '/alumnos?accion=nuevo')

    expect(wrapper.getComponent({ name: 'AlumnoForm' }).props('open')).toBe(true)
    expect(router.currentRoute.value.query.accion).toBeUndefined()
  })

  it('abre cuotas masivas y descarta acciones inválidas o sin permiso', async () => {
    const valid = await mountAt(AlumnosView, '/alumnos?accion=cuotas-masivas')
    expect(valid.wrapper.getComponent({ name: 'GenerarCuotasMasivasModal' }).props('open')).toBe(true)
    expect(valid.router.currentRoute.value.query.accion).toBeUndefined()

    routeState.role = 'consulta'
    const unauthorized = await mountAt(AlumnosView, '/alumnos?accion=nuevo')
    expect(unauthorized.wrapper.getComponent({ name: 'AlumnoForm' }).props('open')).toBe(false)
    expect(unauthorized.router.currentRoute.value.query.accion).toBeUndefined()

    const invalid = await mountAt(AlumnosView, '/alumnos?accion=desconocida')
    expect(invalid.wrapper.getComponent({ name: 'AlumnoForm' }).props('open')).toBe(false)
    expect(invalid.router.currentRoute.value.query.accion).toBeUndefined()
  })

  it('abre la ficha en móvil y al volver conserva filtros, página, desplazamiento y foco', async () => {
    document.body.innerHTML = ''
    const alumno = { id: 41, nombre: 'Ana', apellido: 'Gómez', legajo: 'P-041', estado: 'inactivo' }
    routeState.alumnosRef.value = [alumno]
    routeState.paginationRef.value = { count: 25, page: 1, pageSize: 10 }
    const scrollTo = vi.fn()
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })))
    vi.stubGlobal('scrollTo', scrollTo)
    Object.defineProperty(window, 'scrollY', { configurable: true, value: 640 })
    const listStub = {
      props: ['alumnos'],
      emits: ['select'],
      template: '<div><button v-for="alumno in alumnos" :key="alumno.id" class="students-row" :data-alumno-id="alumno.id" @click="$emit(\'select\', alumno)">{{ alumno.nombre }}</button></div>',
    }
    const { wrapper } = await mountAt(AlumnosView, '/alumnos', { AlumnoList: listStub }, document.body)

    await wrapper.get('input[type="search"]').setValue('Ana')
    await wrapper.findAll('.students-filters select')[2].setValue('inactivo')
    await new Promise((resolve) => setTimeout(resolve, 280))
    await flushPromises()
    await wrapper.get('.students-pagination button:last-child').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Página 2 de 3')

    await wrapper.get('.students-row').trigger('click')
    await flushPromises()
    expect(wrapper.get('section.students-screen').classes()).toContain('students-screen--mobile-detail')
    expect(wrapper.get('.students-mobile-back').text()).toContain('Volver al directorio')

    await wrapper.get('.students-mobile-back').trigger('click')
    await flushPromises()
    expect(wrapper.get('input[type="search"]').element.value).toBe('Ana')
    expect(wrapper.findAll('.students-filters select')[2].element.value).toBe('inactivo')
    expect(wrapper.text()).toContain('Página 2 de 3')
    expect(scrollTo).toHaveBeenLastCalledWith(0, 640)
    expect(document.activeElement.dataset.alumnoId).toBe('41')

    wrapper.unmount()
    vi.unstubAllGlobals()
  })
})

describe('acciones profundas de Caja', () => {
  beforeEach(() => {
    routeState.role = 'administracion'
    routeState.cashStatus = 'abierta'
    routeState.toastErrors = []
  })

  it('abre el movimiento indicado y limpia accion', async () => {
    const { wrapper, router } = await mountAt(CajaView, '/caja?accion=ingreso')

    expect(wrapper.getComponent({ name: 'MovimientoForm' }).props('tipoInicial')).toBe('ingreso')
    expect(router.currentRoute.value.query.accion).toBeUndefined()
  })

  it('descarta acciones inválidas y avisa cuando la caja no está abierta', async () => {
    routeState.cashStatus = 'cerrada'
    const closed = await mountAt(CajaView, '/caja?accion=cerrar')
    expect(closed.wrapper.getComponent({ name: 'CerrarCajaModal' }).props('open')).toBe(false)
    expect(routeState.toastErrors).toContain('La caja del día debe estar abierta para realizar esta operación.')
    expect(closed.router.currentRoute.value.query.accion).toBeUndefined()

    routeState.cashStatus = 'abierta'
    const invalid = await mountAt(CajaView, '/caja?accion=desconocida')
    expect(invalid.wrapper.getComponent({ name: 'MovimientoForm' }).props('open')).toBe(false)
    expect(invalid.router.currentRoute.value.query.accion).toBeUndefined()
  })
})

describe('secciones profundas de Reportes', () => {
  it('sincroniza seccion con pestañas y navegación atrás/adelante', async () => {
    const { wrapper, router } = await mountAt(ReportesView, '/reportes?seccion=caja')
    const tab = (label) => wrapper.findAll('.reports-tabs button').find((button) => button.text() === label)

    expect(tab('Caja').classes()).toContain('active')
    expect(tab('Caja').attributes('aria-current')).toBe('page')
    await tab('Alumnos').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.query.seccion).toBe('alumnos')

    await router.push('/reportes?seccion=morosidad')
    await flushPromises()
    expect(tab('Morosidad').classes()).toContain('active')
  })
})
