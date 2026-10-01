import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AlumnoForm from './AlumnoForm.vue'
import GenerarCuotasMasivasModal from './GenerarCuotasMasivasModal.vue'

const authState = vi.hoisted(() => ({ profile: null, userRef: null }))
const catalogState = vi.hoisted(() => ({ rows: [], branchesRef: null }))
const bulkState = vi.hoisted(() => ({ detail: [], eligible: [], found: 0, omitted: 0 }))

vi.mock('@/composables/useAuth', async () => {
  const { ref } = await import('vue')
  const user = ref(null)
  authState.userRef = user
  return { useAuth: () => ({ user }) }
})

vi.mock('@/composables/useCatalogos', async () => {
  const { ref } = await import('vue')
  const sucursales = ref([])
  catalogState.branchesRef = sucursales
  return {
    useCatalogos: () => ({ sucursales, tiposDescuento: ref([]) }),
  }
})

vi.mock('@/composables/useAlumnos', () => ({
  useAlumnos: () => ({ createAlumno: vi.fn(), updateAlumno: vi.fn() }),
}))

vi.mock('@/composables/useCuotasMasivas', async () => {
  const { ref } = await import('vue')
  return {
    useCuotasMasivas: () => ({
      alumnosElegibles: ref(bulkState.eligible),
      alumnosEncontrados: ref(bulkState.found),
      omitidas: ref(bulkState.omitted),
      detalleAlumnos: ref(bulkState.detail),
      periodos: ref([]),
      etiquetasPeriodo: ref([]),
      cuotasAGenerar: ref(0),
      loading: ref(false),
      error: ref(''),
      evaluar: vi.fn(async () => {}),
      generar: vi.fn(async () => []),
    }),
  }
})

vi.mock('@/composables/useToast', () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }))
vi.mock('@/lib/swal', () => ({
  confirmGeneracionCuotasMasivas: vi.fn(async () => ({ isConfirmed: false })),
  showResultadoCuotasMasivas: vi.fn(),
}))

const activeBranch = { id: 2, nombre: 'Posadas' }
const otherBranch = { id: 1, nombre: 'Eldorado' }

function mountForm(component, props = {}) {
  const componentProps = {
    open: true,
    sucursales: [otherBranch, activeBranch],
    ...props,
  }
  if (component === AlumnoForm) delete componentProps.sucursales
  return mount(component, {
    props: componentProps,
    attachTo: document.body,
    global: {
      stubs: {
        AppModalTransition: { template: '<div><slot /></div>' },
        AppButtonContent: { props: ['label'], template: '<span>{{ label }}</span>' },
      },
      directives: {
        'focus-trap': {},
        'form-validation': {},
      },
    },
  })
}

describe('sucursal inicial en formularios de alumnos y cobranzas', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    catalogState.branchesRef.value = [otherBranch, activeBranch]
    authState.userRef.value = { perfil: { sucursal: { id: activeBranch.id } } }
    bulkState.detail = []
    bulkState.eligible = []
    bulkState.found = 0
    bulkState.omitted = 0
  })

  it('preselecciona la sucursal del perfil para crear alumnos', async () => {
    const wrapper = mountForm(AlumnoForm)
    await flushPromises()

    expect(document.querySelector('select').value).toBe(String(activeBranch.id))
    wrapper.unmount()
  })

  it('deja vacía la sucursal si el perfil no tiene una opción autorizada', async () => {
    authState.userRef.value = { perfil: { sucursal: { id: 99 } } }
    const wrapper = mountForm(AlumnoForm)
    await flushPromises()

    expect(document.querySelector('select').value).toBe('')
    wrapper.unmount()
  })

  it('preselecciona la sucursal del perfil para la generación masiva', async () => {
    const wrapper = mountForm(GenerarCuotasMasivasModal)
    await flushPromises()

    expect(document.querySelector('select').value).toBe(String(activeBranch.id))
    wrapper.unmount()
  })

  it('mantiene la sucursal sin seleccionar cuando el perfil no coincide con el catálogo', async () => {
    authState.userRef.value = { perfil: { sucursal: null } }
    const wrapper = mountForm(GenerarCuotasMasivasModal)
    await flushPromises()

    expect(document.querySelector('select').value).toBe('')
    wrapper.unmount()
  })

  it('presenta elegibles y omitidos con páginas locales de diez filas y resumen repetible', async () => {
    const eligible = Array.from({ length: 12 }, (_, index) => ({
      id: index + 1,
      legajo: `P-${String(index + 1).padStart(3, '0')}`,
      nombre_completo: `Alumno ${index + 1}`,
      carrera_nombre: 'Enfermería',
      estado: 'activo',
      motivo: '',
    }))
    const omitted = [13, 14].map((id) => ({
      id,
      legajo: `P-${id}`,
      nombre_completo: `Alumno ${id}`,
      carrera_nombre: 'Enfermería',
      estado: 'activo',
      motivo: 'Ya existe una cuota para este concepto y período.',
    }))
    bulkState.detail = [...eligible, ...omitted]
    bulkState.eligible = eligible
    bulkState.found = 14
    bulkState.omitted = 2
    const wrapper = mountForm(GenerarCuotasMasivasModal, {
      conceptos: [{ id: 10, nombre: 'Cuota mensual', activo: true, sucursal: activeBranch.id, importe: '100.00' }],
      carreras: [{ id: 5, nombre: 'Enfermería', sucursal: activeBranch.id }],
    })
    await flushPromises()

    expect(document.querySelector('.massive-fee-summary').textContent).toContain('12 alumnos elegibles')
    expect(document.querySelector('.massive-fee-summary').textContent).toContain('2 omitidos')
    expect(document.querySelector('.massive-fee-summary').textContent).toContain('Posadas')
    expect(document.querySelector('.massive-fee-summary').textContent).toContain('Cuota mensual')
    expect(document.querySelector('.massive-fee-summary').textContent).toMatch(/1\.200,00/)
    expect(document.querySelectorAll('#massive-fee-preview-list > li')).toHaveLength(10)

    document.querySelector('.massive-fee-preview-pagination button:last-child').click()
    await flushPromises()
    expect(document.querySelectorAll('#massive-fee-preview-list > li')).toHaveLength(2)
    expect(document.querySelector('#massive-fee-preview-list').textContent).toContain('Alumno 11')

    document.querySelector('#massive-fee-omitted-tab').click()
    await flushPromises()
    expect(document.querySelector('#massive-fee-omitted-tab').getAttribute('aria-selected')).toBe('true')
    expect(document.querySelectorAll('#massive-fee-preview-list > li')).toHaveLength(2)
    expect(document.querySelector('#massive-fee-preview-list').textContent).toContain('Ya existe una cuota')
    expect(document.querySelector('#massive-fee-preview-list').textContent).not.toContain('DNI')
    wrapper.unmount()
  })
})
