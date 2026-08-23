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
  return {
    useAlumnos: () => ({
      alumnos,
      selectedAlumno,
      pagination,
      alumnoStats,
      loading: ref(false),
      error: ref(''),
      setSelected: vi.fn(),
      loadAlumnos: vi.fn(async () => {}),
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
      loading: ref(false),
      error: ref(''),
      loadResumen: vi.fn(async () => {}),
      loadPagos: vi.fn(async () => {}),
      loadCobranzasUsuarios: vi.fn(async () => {}),
      exportarExcel: vi.fn(),
    }),
  }
})

async function mountAt(component, path) {
  const routePath = path.split('?')[0]
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: routePath, component: { template: '<div />' } }],
  })
  await router.push(path)
  await router.isReady()
  const wrapper = shallowMount(component, { global: { plugins: [router] } })
  await flushPromises()
  return { wrapper, router }
}

describe('acciones profundas de Alumnos', () => {
  beforeEach(() => {
    routeState.role = 'administracion'
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
    expect(closed.wrapper.findComponent({ name: 'CerrarCajaModal' }).exists()).toBe(false)
    expect(routeState.toastErrors).toContain('La caja del día debe estar abierta para realizar esta operación.')
    expect(closed.router.currentRoute.value.query.accion).toBeUndefined()

    routeState.cashStatus = 'abierta'
    const invalid = await mountAt(CajaView, '/caja?accion=desconocida')
    expect(invalid.wrapper.findComponent({ name: 'MovimientoForm' }).exists()).toBe(false)
    expect(invalid.router.currentRoute.value.query.accion).toBeUndefined()
  })
})

describe('secciones profundas de Reportes', () => {
  it('sincroniza seccion con pestañas y navegación atrás/adelante', async () => {
    const { wrapper, router } = await mountAt(ReportesView, '/reportes?seccion=caja')
    const tab = (label) => wrapper.findAll('.reports-tabs button').find((button) => button.text() === label)

    expect(tab('Caja').classes()).toContain('active')
    await tab('Alumnos').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.query.seccion).toBe('alumnos')

    await router.push('/reportes?seccion=morosidad')
    await flushPromises()
    expect(tab('Morosidad').classes()).toContain('active')
  })
})
