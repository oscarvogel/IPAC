<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const token = ref(localStorage.getItem('ipac_token') || '')
const user = ref(null)
const loading = ref(false)
const error = ref('')
const activeModule = ref('alumnos')
const searchQuery = ref('')
const sucursalFilter = ref('todas')
const selectedAlumnoId = ref(null)
const showAlumnoModal = ref(false)
const editingAlumnoId = ref(null)
const showPagoModal = ref(false)
const showEstadoModal = ref(false)
const showMovimientoModal = ref(false)
const showCerrarCajaModal = ref(false)
const editingConceptoId = ref(null)

const loginForm = reactive({
  username: '',
  password: '',
})

const sucursales = ref([])
const carreras = ref([])
const alumnos = ref([])
const conceptos = ref([])
const pagos = ref([])
const cajaHoy = ref(null)

const alumnoForm = reactive({
  legajo: '',
  nombre: '',
  apellido: '',
  dni: '',
  email: '',
  telefono: '',
  sucursal: '',
  carrera: '',
})

const conceptoForm = reactive({
  nombre: '',
  tipo: 'cuota',
  importe: '',
  sucursal: '',
  carrera: '',
})

const pagoForm = reactive({
  concepto: '',
  importe: '',
  medio: 'efectivo',
  observacion: '',
})

const movimientoForm = reactive({
  tipo: 'egreso',
  medio: 'efectivo',
  importe: '',
  descripcion: '',
})

const cierreForm = reactive({
  total_contado: '',
})

const modules = [
  { id: 'alumnos', label: 'Alumnos', meta: 'CRM' },
  { id: 'caja', label: 'Caja', meta: 'Tesoreria' },
  { id: 'conceptos', label: 'Conceptos', meta: 'Aranceles' },
  { id: 'sucursales', label: 'Sucursales', meta: 'Accesos' },
]

const isAuthenticated = computed(() => Boolean(token.value && user.value))

const filteredAlumnos = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return alumnos.value.filter((alumno) => {
    const matchesSucursal = sucursalFilter.value === 'todas' || String(alumno.sucursal) === String(sucursalFilter.value)
    const text = `${alumno.legajo} ${alumno.nombre} ${alumno.apellido} ${alumno.dni} ${alumno.email} ${alumno.sucursal_nombre}`.toLowerCase()
    return matchesSucursal && (!query || text.includes(query))
  })
})

const selectedAlumno = computed(() => {
  if (!filteredAlumnos.value.length) return null
  return filteredAlumnos.value.find((alumno) => alumno.id === selectedAlumnoId.value) || filteredAlumnos.value[0]
})

const dashboardStats = computed(() => [
  { label: 'Alumnos activos', value: alumnos.value.length, detail: 'base inicial cargada' },
  { label: 'Sucursales', value: sucursales.value.length, detail: 'Posadas y Eldorado' },
  { label: 'Pagos registrados', value: pagos.value.length, detail: 'movimientos cargados' },
  { label: 'Pendientes demo', value: `$ ${formatMoney(totalSaldoDemo.value)}`, detail: 'saldo estimado' },
])

const detailConcepts = computed(() => {
  const activos = conceptos.value.filter((concepto) => concepto.activo)
  if (!selectedAlumno.value) return activos.slice(0, 3)
  return activos.filter((concepto) => concepto.sucursal === selectedAlumno.value.sucursal).slice(0, 3)
})

const conceptosActivos = computed(() => conceptos.value.filter((concepto) => concepto.activo))

const selectedPagos = computed(() => {
  if (!selectedAlumno.value) return []
  return pagos.value.filter((pago) => pago.alumno === selectedAlumno.value.id)
})

const selectedTotalConceptos = computed(() =>
  detailConcepts.value.reduce((total, concepto) => total + Number(concepto.importe || 0), 0),
)

const selectedTotalPagado = computed(() =>
  selectedPagos.value.reduce((total, pago) => total + Number(pago.importe || 0), 0),
)

const selectedSaldo = computed(() => Math.max(selectedTotalConceptos.value - selectedTotalPagado.value, 0))

const totalSaldoDemo = computed(() => {
  return alumnos.value.reduce((total, alumno) => {
    const conceptosAlumno = conceptos.value.filter((concepto) => concepto.sucursal === alumno.sucursal)
    const pagosAlumno = pagos.value.filter((pago) => pago.alumno === alumno.id)
    const debe = conceptosAlumno.reduce((acc, concepto) => acc + Number(concepto.importe || 0), 0)
    const pago = pagosAlumno.reduce((acc, item) => acc + Number(item.importe || 0), 0)
    return total + Math.max(debe - pago, 0)
  }, 0)
})

const cajaMovimientos = computed(() => cajaHoy.value?.movimientos || [])
const cajaTotales = computed(() => {
  return cajaMovimientos.value.reduce(
    (acc, movimiento) => {
      const amount = Number(movimiento.importe || 0)
      const signed = ['egreso', 'retiro', 'pase'].includes(movimiento.tipo) ? -amount : amount
      acc.total += signed
      acc[movimiento.medio] = (acc[movimiento.medio] || 0) + signed
      return acc
    },
    { total: 0, efectivo: 0, transferencia: 0, tarjeta: 0, otro: 0 },
  )
})

function formatMoney(value) {
  return Number(value || 0).toLocaleString('es-AR', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })
}

async function apiRequest(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  if (token.value) {
    headers.Authorization = `Token ${token.value}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 204) return null

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const detail = data.detail || data.non_field_errors?.join(' ') || 'No se pudo completar la operacion.'
    throw new Error(detail)
  }

  return data
}

function resetAlumnoForm() {
  Object.assign(alumnoForm, {
    legajo: '',
    nombre: '',
    apellido: '',
    dni: '',
    email: '',
    telefono: '',
    sucursal: sucursales.value[0]?.id || '',
    carrera: '',
  })
}

function openNewAlumnoModal() {
  editingAlumnoId.value = null
  resetAlumnoForm()
  showAlumnoModal.value = true
}

function openEditAlumnoModal(alumno = selectedAlumno.value) {
  if (!alumno) return
  editingAlumnoId.value = alumno.id
  Object.assign(alumnoForm, {
    legajo: alumno.legajo,
    nombre: alumno.nombre,
    apellido: alumno.apellido,
    dni: alumno.dni,
    email: alumno.email || '',
    telefono: alumno.telefono || '',
    sucursal: alumno.sucursal,
    carrera: alumno.carrera || '',
  })
  showAlumnoModal.value = true
}

function closeAlumnoModal() {
  showAlumnoModal.value = false
  editingAlumnoId.value = null
  resetAlumnoForm()
}

function resetPagoForm() {
  const firstConcept = detailConcepts.value[0]
  Object.assign(pagoForm, {
    concepto: firstConcept?.id || '',
    importe: firstConcept?.importe || '',
    medio: 'efectivo',
    observacion: '',
  })
}

function openPagoModal() {
  if (!selectedAlumno.value) return
  resetPagoForm()
  showPagoModal.value = true
}

function closePagoModal() {
  showPagoModal.value = false
  resetPagoForm()
}

function resetConceptoForm() {
  editingConceptoId.value = null
  Object.assign(conceptoForm, {
    nombre: '',
    tipo: 'cuota',
    importe: '',
    sucursal: sucursales.value[0]?.id || '',
    carrera: '',
  })
}

function editConcepto(concepto) {
  editingConceptoId.value = concepto.id
  Object.assign(conceptoForm, {
    nombre: concepto.nombre,
    tipo: concepto.tipo,
    importe: concepto.importe,
    sucursal: concepto.sucursal,
    carrera: concepto.carrera || '',
  })
}

async function loadCatalogs() {
  const [sucursalesData, carrerasData, alumnosData, conceptosData, pagosData] = await Promise.all([
    apiRequest('/sucursales/'),
    apiRequest('/carreras/'),
    apiRequest('/alumnos/'),
    apiRequest('/conceptos/'),
    apiRequest('/pagos/'),
  ])

  sucursales.value = sucursalesData.results || []
  carreras.value = carrerasData.results || []
  alumnos.value = alumnosData.results || []
  conceptos.value = conceptosData.results || []
  pagos.value = pagosData.results || []

  if (!alumnoForm.sucursal) resetAlumnoForm()
  if (!conceptoForm.sucursal) resetConceptoForm()
  if (!selectedAlumnoId.value && alumnos.value[0]) selectedAlumnoId.value = alumnos.value[0].id
  await loadCajaHoy()
}

async function loadCajaHoy() {
  const sucursalId = user.value?.perfil?.sucursal?.id || sucursales.value[0]?.id
  if (!sucursalId) return
  cajaHoy.value = await apiRequest(`/cajas/hoy/?sucursal=${sucursalId}`)
}

async function loadSession() {
  if (!token.value) return
  try {
    user.value = await apiRequest('/auth/me/')
    await loadCatalogs()
  } catch (err) {
    logout()
  }
}

async function login() {
  error.value = ''
  loading.value = true

  try {
    const data = await apiRequest('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(loginForm),
    })
    token.value = data.key
    localStorage.setItem('ipac_token', data.key)
    user.value = await apiRequest('/auth/me/')
    await loadCatalogs()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function logout() {
  token.value = ''
  user.value = null
  localStorage.removeItem('ipac_token')
}

function selectAlumno(alumno) {
  selectedAlumnoId.value = alumno.id
}

async function createAlumno() {
  error.value = ''
  loading.value = true
  try {
    const payload = {
      ...alumnoForm,
      carrera: alumnoForm.carrera || null,
    }
    const saved = await apiRequest(
      editingAlumnoId.value ? `/alumnos/${editingAlumnoId.value}/` : '/alumnos/',
      {
        method: editingAlumnoId.value ? 'PATCH' : 'POST',
        body: JSON.stringify(payload),
      },
    )
    const savedId = saved.id
    closeAlumnoModal()
    await loadCatalogs()
    selectedAlumnoId.value = savedId
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function saveConcepto() {
  error.value = ''
  loading.value = true
  try {
    const isEditing = Boolean(editingConceptoId.value)
    await apiRequest(isEditing ? `/conceptos/${editingConceptoId.value}/` : '/conceptos/', {
      method: isEditing ? 'PUT' : 'POST',
      body: JSON.stringify({
        ...conceptoForm,
        carrera: conceptoForm.carrera || null,
      }),
    })
    resetConceptoForm()
    await loadCatalogs()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function desactivarConcepto(concepto) {
  if (!window.confirm(`¿Desactivar el concepto "${concepto.nombre}"? Dejara de estar disponible para nuevos cobros.`)) return
  error.value = ''
  loading.value = true
  try {
    await apiRequest(`/conceptos/${concepto.id}/`, { method: 'DELETE' })
    if (editingConceptoId.value === concepto.id) resetConceptoForm()
    await loadCatalogs()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function createPago() {
  if (!selectedAlumno.value) return
  error.value = ''
  loading.value = true
  try {
    await apiRequest('/pagos/', {
      method: 'POST',
      body: JSON.stringify({
        alumno: selectedAlumno.value.id,
        concepto: pagoForm.concepto || null,
        importe: pagoForm.importe,
        medio: pagoForm.medio,
        observacion: pagoForm.observacion,
      }),
    })
    closePagoModal()
    await loadCatalogs()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function openMovimientoModal(tipo = 'egreso') {
  Object.assign(movimientoForm, {
    tipo,
    medio: 'efectivo',
    importe: '',
    descripcion: '',
  })
  showMovimientoModal.value = true
}

function closeMovimientoModal() {
  showMovimientoModal.value = false
}

async function createMovimientoCaja() {
  if (!cajaHoy.value) return
  error.value = ''
  loading.value = true
  try {
    await apiRequest('/movimientos-caja/', {
      method: 'POST',
      body: JSON.stringify({
        caja: cajaHoy.value.id,
        tipo: movimientoForm.tipo,
        medio: movimientoForm.medio,
        importe: movimientoForm.importe,
        descripcion: movimientoForm.descripcion,
      }),
    })
    closeMovimientoModal()
    await loadCajaHoy()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function openCerrarCajaModal() {
  cierreForm.total_contado = cajaTotales.value.total.toFixed(2)
  showCerrarCajaModal.value = true
}

async function cerrarCaja() {
  if (!cajaHoy.value) return
  error.value = ''
  loading.value = true
  try {
    cajaHoy.value = await apiRequest(`/cajas/${cajaHoy.value.id}/cerrar/`, {
      method: 'POST',
      body: JSON.stringify({ total_contado: cierreForm.total_contado }),
    })
    showCerrarCajaModal.value = false
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

watch(filteredAlumnos, (items) => {
  if (!items.length) {
    selectedAlumnoId.value = null
    return
  }
  if (!items.some((item) => item.id === selectedAlumnoId.value)) {
    selectedAlumnoId.value = items[0].id
  }
})

onMounted(loadSession)
</script>

<template>
  <main class="app-shell">
    <section v-if="!isAuthenticated" class="login-screen">
      <div class="login-panel">
        <div class="login-copy">
          <span class="brand-mark">IP</span>
          <p class="eyebrow">IPAC CRM</p>
          <h1>Administracion y cobranzas en una sola vista.</h1>
          <p>
            Un panel para encontrar alumnos, revisar sucursal, cargar datos y
            preparar el flujo de caja sin perder contexto.
          </p>
        </div>

        <form class="login-card" @submit.prevent="login">
          <h2>Ingresar</h2>
          <label>
            Usuario
            <input v-model="loginForm.username" autocomplete="username" required />
          </label>
          <label>
            Clave
            <input v-model="loginForm.password" type="password" autocomplete="current-password" required />
          </label>
          <p v-if="error" class="alert">{{ error }}</p>
          <button class="primary-button" type="submit" :disabled="loading">
            {{ loading ? 'Ingresando...' : 'Entrar al CRM' }}
          </button>
        </form>
      </div>
    </section>

    <template v-else>
      <aside class="sidebar">
        <div class="brand-block">
          <span class="brand-mark">IP</span>
          <div>
            <p class="brand">IPAC</p>
            <small>CRM administrativo</small>
          </div>
        </div>

        <nav class="main-nav">
          <button
            v-for="module in modules"
            :key="module.id"
            :class="{ active: activeModule === module.id }"
            type="button"
            @click="activeModule = module.id"
          >
            <span>{{ module.label }}</span>
            <small>{{ module.meta }}</small>
          </button>
        </nav>

        <div class="sidebar-footer">
          <small>{{ user.perfil.sucursal.nombre }}</small>
          <strong>{{ user.username }}</strong>
          <button type="button" @click="logout">Salir</button>
        </div>
      </aside>

      <section class="workspace">
        <header class="topbar">
          <div>
            <p class="eyebrow">Panel de trabajo</p>
            <h1>{{ activeModule === 'alumnos' ? 'Alumnos' : modules.find((module) => module.id === activeModule)?.label }}</h1>
          </div>
          <div class="top-actions">
            <input v-model="searchQuery" class="global-search" placeholder="Buscar alumno, DNI, legajo..." />
            <select v-model="sucursalFilter" class="compact-select">
              <option value="todas">Todas las sucursales</option>
              <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
                {{ sucursal.nombre }}
              </option>
            </select>
            <button
              v-if="activeModule === 'alumnos'"
              class="new-button"
              type="button"
              @click="openNewAlumnoModal"
            >
              Nuevo alumno
            </button>
          </div>
        </header>

        <p v-if="error" class="alert">{{ error }}</p>

        <section v-if="activeModule === 'alumnos'" class="crm-screen">
          <div class="stats-grid">
            <article v-for="stat in dashboardStats" :key="stat.label" class="stat-card">
              <span>{{ stat.label }}</span>
              <strong>{{ stat.value }}</strong>
              <small>{{ stat.detail }}</small>
            </article>
          </div>

          <section class="crm-grid">
            <div class="crm-list panel">
              <div class="panel-head">
                <div>
                  <h2>Lista inteligente</h2>
                  <p>{{ filteredAlumnos.length }} alumnos visibles</p>
                </div>
                <div class="status-tabs">
                  <span class="active">Todos</span>
                  <span>Con deuda</span>
                  <span>Nuevos</span>
                </div>
              </div>

              <div class="student-list">
                <button
                  v-for="alumno in filteredAlumnos"
                  :key="alumno.id"
                  :class="{ selected: selectedAlumno?.id === alumno.id }"
                  class="student-row"
                  type="button"
                  @click="selectAlumno(alumno)"
                >
                  <span class="avatar">{{ alumno.nombre.slice(0, 1) }}{{ alumno.apellido.slice(0, 1) }}</span>
                  <span>
                    <strong>{{ alumno.apellido }}, {{ alumno.nombre }}</strong>
                    <small>{{ alumno.legajo }} · {{ alumno.carrera_nombre || 'Sin carrera asignada' }}</small>
                  </span>
                  <span class="row-meta">
                    <small>{{ alumno.sucursal_nombre }}</small>
                    <em>{{ alumno.estado }}</em>
                  </span>
                </button>

                <div v-if="!filteredAlumnos.length" class="empty-state">
                  No hay alumnos para el filtro actual.
                </div>
              </div>
            </div>

            <aside class="detail-panel panel">
              <template v-if="selectedAlumno">
                <div class="detail-hero">
                  <span class="avatar large">{{ selectedAlumno.nombre.slice(0, 1) }}{{ selectedAlumno.apellido.slice(0, 1) }}</span>
                  <div>
                    <p class="eyebrow">Cuenta del alumno</p>
                    <h2>{{ selectedAlumno.nombre }} {{ selectedAlumno.apellido }}</h2>
                    <small>{{ selectedAlumno.legajo }} · DNI {{ selectedAlumno.dni }}</small>
                  </div>
                </div>

                <div class="detail-actions">
                  <button type="button" @click="openPagoModal">Registrar pago</button>
                  <button type="button" @click="openEditAlumnoModal()">Editar alumno</button>
                </div>

                <dl class="detail-data">
                  <div><dt>Sucursal</dt><dd>{{ selectedAlumno.sucursal_nombre }}</dd></div>
                  <div><dt>Carrera</dt><dd>{{ selectedAlumno.carrera_nombre || 'Sin asignar' }}</dd></div>
                  <div><dt>Email</dt><dd>{{ selectedAlumno.email || 'Sin email' }}</dd></div>
                  <div><dt>Telefono</dt><dd>{{ selectedAlumno.telefono || 'Sin telefono' }}</dd></div>
                </dl>

                <div class="mini-ledger">
                  <div class="panel-head compact">
                    <h3>Conceptos asociados</h3>
                    <span>{{ detailConcepts.length }}</span>
                  </div>
                  <div v-for="concepto in detailConcepts" :key="concepto.id" class="ledger-row">
                    <span>{{ concepto.nombre }}</span>
                    <strong>$ {{ concepto.importe }}</strong>
                  </div>
                </div>

                <div class="account-summary">
                  <div><span>Pagado</span><strong>$ {{ formatMoney(selectedTotalPagado) }}</strong></div>
                  <div><span>Saldo</span><strong>$ {{ formatMoney(selectedSaldo) }}</strong></div>
                  <button type="button" @click="showEstadoModal = true">Ver estado de cuenta</button>
                </div>
              </template>
            </aside>

          </section>
        </section>

        <section v-if="activeModule === 'conceptos'" class="secondary-grid">
          <form class="panel quick-create" @submit.prevent="saveConcepto">
            <div class="panel-head compact">
              <h2>{{ editingConceptoId ? 'Editar concepto' : 'Nuevo concepto' }}</h2>
              <span>{{ editingConceptoId ? 'Edicion' : 'Arancel' }}</span>
            </div>
            <div class="quick-form">
              <label>Nombre<input v-model="conceptoForm.nombre" required /></label>
              <label>
                Tipo
                <select v-model="conceptoForm.tipo">
                  <option value="matricula">Matricula</option>
                  <option value="cuota">Cuota</option>
                  <option value="material">Material</option>
                  <option value="otro">Otro</option>
                </select>
              </label>
              <label>Importe<input v-model="conceptoForm.importe" type="number" min="0" step="0.01" required /></label>
              <label>
                Sucursal
                <select v-model="conceptoForm.sucursal" required>
                  <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
                    {{ sucursal.nombre }}
                  </option>
                </select>
              </label>
            </div>
            <div class="form-actions">
              <button v-if="editingConceptoId" class="secondary-button" :disabled="loading" type="button" @click="resetConceptoForm">Cancelar</button>
              <button class="primary-button" :disabled="loading" type="submit">{{ editingConceptoId ? 'Guardar cambios' : 'Guardar concepto' }}</button>
            </div>
          </form>

          <div class="panel table-card">
            <div class="panel-head">
              <div>
                <h2>Conceptos activos</h2>
                <p>{{ conceptosActivos.length }} activos · {{ conceptos.length - conceptosActivos.length }} inactivos</p>
              </div>
            </div>
            <table>
              <thead>
                <tr><th>Nombre</th><th>Tipo</th><th>Importe</th><th>Sucursal</th><th>Acciones</th></tr>
              </thead>
              <tbody>
                <tr v-for="concepto in conceptos" :key="concepto.id">
                  <td>{{ concepto.nombre }}</td>
                  <td>{{ concepto.tipo }}</td>
                  <td>$ {{ concepto.importe }}</td>
                  <td>{{ concepto.sucursal_nombre }}</td>
                  <td class="table-actions">
                    <button class="secondary-button" type="button" @click="editConcepto(concepto)">Editar</button>
                    <button class="danger-button" type="button" @click="desactivarConcepto(concepto)">Desactivar</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section v-if="activeModule === 'caja'" class="cash-screen">
          <div class="cash-hero panel">
            <div>
              <p class="eyebrow">Caja del dia</p>
              <h2>{{ cajaHoy?.sucursal_nombre || user.perfil.sucursal.nombre }}</h2>
              <span>{{ cajaHoy?.fecha }} · {{ cajaHoy?.estado }}</span>
            </div>
            <div class="cash-actions">
              <button type="button" @click="openMovimientoModal('ingreso')" :disabled="cajaHoy?.estado === 'cerrada'">Ingreso</button>
              <button type="button" @click="openMovimientoModal('egreso')" :disabled="cajaHoy?.estado === 'cerrada'">Egreso</button>
              <button type="button" @click="openMovimientoModal('retiro')" :disabled="cajaHoy?.estado === 'cerrada'">Retiro</button>
              <button class="close-cash" type="button" @click="openCerrarCajaModal" :disabled="cajaHoy?.estado === 'cerrada'">Cerrar caja</button>
            </div>
          </div>

          <div class="stats-grid cash-stats">
            <article class="stat-card"><span>Total esperado</span><strong>$ {{ formatMoney(cajaTotales.total) }}</strong><small>incluye pagos y movimientos</small></article>
            <article class="stat-card"><span>Efectivo</span><strong>$ {{ formatMoney(cajaTotales.efectivo) }}</strong><small>saldo de efectivo</small></article>
            <article class="stat-card"><span>Transferencia</span><strong>$ {{ formatMoney(cajaTotales.transferencia) }}</strong><small>pagos bancarios</small></article>
            <article class="stat-card"><span>Movimientos</span><strong>{{ cajaMovimientos.length }}</strong><small>registrados hoy</small></article>
          </div>

          <div class="panel table-card">
            <div class="panel-head">
              <div>
                <h2>Movimientos de caja</h2>
                <p>Pagos, ingresos, egresos, retiros y pases</p>
              </div>
            </div>
            <table>
              <thead>
                <tr><th>Tipo</th><th>Medio</th><th>Descripcion</th><th>Importe</th></tr>
              </thead>
              <tbody>
                <tr v-for="movimiento in cajaMovimientos" :key="movimiento.id">
                  <td><span class="table-badge">{{ movimiento.tipo_label }}</span></td>
                  <td>{{ movimiento.medio }}</td>
                  <td>{{ movimiento.descripcion || 'Sin descripcion' }}</td>
                  <td>$ {{ formatMoney(movimiento.importe) }}</td>
                </tr>
              </tbody>
            </table>
            <p v-if="!cajaMovimientos.length" class="empty-state flat">Todavia no hay movimientos en esta caja.</p>
          </div>
        </section>

        <section v-if="activeModule === 'sucursales'" class="panel table-card">
          <div class="panel-head">
            <div>
              <h2>Sucursales</h2>
              <p>Visibilidad y operacion por sede</p>
            </div>
          </div>
          <table>
            <thead>
              <tr><th>Codigo</th><th>Nombre</th><th>Estado</th></tr>
            </thead>
            <tbody>
              <tr v-for="sucursal in sucursales" :key="sucursal.id">
                <td>{{ sucursal.codigo }}</td>
                <td>{{ sucursal.nombre }}</td>
                <td><span class="table-badge">{{ sucursal.activa ? 'Activa' : 'Inactiva' }}</span></td>
              </tr>
            </tbody>
          </table>
        </section>

        <Teleport to="body">
          <div v-if="showAlumnoModal" class="modal-backdrop" @click.self="closeAlumnoModal">
            <form class="modal-card" @submit.prevent="createAlumno">
              <header class="modal-head">
                <div>
                  <p class="eyebrow">{{ editingAlumnoId ? 'Edicion de alumno' : 'Alta de alumno' }}</p>
                  <h2>{{ editingAlumnoId ? 'Editar alumno' : 'Nuevo alumno' }}</h2>
                  <span>{{ editingAlumnoId ? 'Actualiza los datos administrativos del alumno seleccionado.' : 'Datos administrativos iniciales para operar en el CRM.' }}</span>
                </div>
                <button class="icon-button" type="button" aria-label="Cerrar" @click="closeAlumnoModal">
                  ×
                </button>
              </header>

              <section class="modal-section">
                <h3>Identificacion</h3>
                <div class="modal-grid">
                  <label>Legajo<input v-model="alumnoForm.legajo" required /></label>
                  <label>DNI<input v-model="alumnoForm.dni" required /></label>
                  <label>Nombre<input v-model="alumnoForm.nombre" required /></label>
                  <label>Apellido<input v-model="alumnoForm.apellido" required /></label>
                </div>
              </section>

              <section class="modal-section">
                <h3>Contacto y cursada</h3>
                <div class="modal-grid">
                  <label>Email<input v-model="alumnoForm.email" type="email" /></label>
                  <label>Telefono<input v-model="alumnoForm.telefono" /></label>
                  <label>
                    Sucursal
                    <select v-model="alumnoForm.sucursal" required>
                      <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
                        {{ sucursal.nombre }}
                      </option>
                    </select>
                  </label>
                  <label>
                    Carrera
                    <select v-model="alumnoForm.carrera">
                      <option value="">Sin asignar</option>
                      <option v-for="carrera in carreras" :key="carrera.id" :value="carrera.id">
                        {{ carrera.nombre }}
                      </option>
                    </select>
                  </label>
                </div>
              </section>

              <footer class="modal-actions">
                <button class="secondary-button" type="button" @click="closeAlumnoModal">Cancelar</button>
                <button class="primary-button modal-submit" :disabled="loading" type="submit">
                  {{ loading ? 'Guardando...' : editingAlumnoId ? 'Guardar cambios' : 'Guardar alumno' }}
                </button>
              </footer>
            </form>
          </div>
        </Teleport>

        <Teleport to="body">
          <div v-if="showPagoModal" class="modal-backdrop" @click.self="closePagoModal">
            <form class="modal-card compact-modal" @submit.prevent="createPago">
              <header class="modal-head">
                <div>
                  <p class="eyebrow">Cobranza</p>
                  <h2>Registrar pago</h2>
                  <span>{{ selectedAlumno?.apellido }}, {{ selectedAlumno?.nombre }}</span>
                </div>
                <button class="icon-button" type="button" aria-label="Cerrar" @click="closePagoModal">×</button>
              </header>

              <section class="modal-section">
                <div class="modal-grid">
                  <label>
                    Concepto
                    <select v-model="pagoForm.concepto">
                      <option value="">Pago a cuenta</option>
                      <option v-for="concepto in detailConcepts" :key="concepto.id" :value="concepto.id">
                        {{ concepto.nombre }} · $ {{ concepto.importe }}
                      </option>
                    </select>
                  </label>
                  <label>Importe<input v-model="pagoForm.importe" type="number" min="0" step="0.01" required /></label>
                  <label>
                    Medio
                    <select v-model="pagoForm.medio">
                      <option value="efectivo">Efectivo</option>
                      <option value="transferencia">Transferencia</option>
                      <option value="tarjeta">Tarjeta</option>
                      <option value="otro">Otro</option>
                    </select>
                  </label>
                  <label>Observacion<input v-model="pagoForm.observacion" /></label>
                </div>
              </section>

              <footer class="modal-actions">
                <button class="secondary-button" type="button" @click="closePagoModal">Cancelar</button>
                <button class="primary-button modal-submit" :disabled="loading" type="submit">
                  {{ loading ? 'Guardando...' : 'Guardar pago' }}
                </button>
              </footer>
            </form>
          </div>
        </Teleport>

        <Teleport to="body">
          <div v-if="showEstadoModal" class="modal-backdrop" @click.self="showEstadoModal = false">
            <section class="modal-card account-modal">
              <header class="modal-head">
                <div>
                  <p class="eyebrow">Estado de cuenta</p>
                  <h2>{{ selectedAlumno?.nombre }} {{ selectedAlumno?.apellido }}</h2>
                  <span>Conceptos, pagos registrados y saldo estimado.</span>
                </div>
                <button class="icon-button" type="button" aria-label="Cerrar" @click="showEstadoModal = false">×</button>
              </header>

              <section class="account-totals">
                <article><span>Conceptos</span><strong>$ {{ formatMoney(selectedTotalConceptos) }}</strong></article>
                <article><span>Pagado</span><strong>$ {{ formatMoney(selectedTotalPagado) }}</strong></article>
                <article><span>Saldo</span><strong>$ {{ formatMoney(selectedSaldo) }}</strong></article>
              </section>

              <section class="modal-section">
                <h3>Pagos registrados</h3>
                <div class="account-list">
                  <div v-for="pago in selectedPagos" :key="pago.id" class="account-row">
                    <div>
                      <strong>{{ pago.concepto_nombre || 'Pago a cuenta' }}</strong>
                      <span>{{ pago.fecha }} · {{ pago.medio }}</span>
                    </div>
                    <strong>$ {{ formatMoney(pago.importe) }}</strong>
                  </div>
                  <p v-if="!selectedPagos.length" class="empty-state flat">Todavia no hay pagos registrados.</p>
                </div>
              </section>
            </section>
          </div>
        </Teleport>

        <Teleport to="body">
          <div v-if="showMovimientoModal" class="modal-backdrop" @click.self="closeMovimientoModal">
            <form class="modal-card compact-modal" @submit.prevent="createMovimientoCaja">
              <header class="modal-head">
                <div>
                  <p class="eyebrow">Movimiento de caja</p>
                  <h2>Registrar {{ movimientoForm.tipo }}</h2>
                  <span>Caja {{ cajaHoy?.sucursal_nombre }} · {{ cajaHoy?.fecha }}</span>
                </div>
                <button class="icon-button" type="button" aria-label="Cerrar" @click="closeMovimientoModal">×</button>
              </header>
              <section class="modal-section">
                <div class="modal-grid">
                  <label>
                    Tipo
                    <select v-model="movimientoForm.tipo">
                      <option value="ingreso">Ingreso</option>
                      <option value="egreso">Egreso</option>
                      <option value="retiro">Retiro</option>
                      <option value="pase">Pase</option>
                    </select>
                  </label>
                  <label>
                    Medio
                    <select v-model="movimientoForm.medio">
                      <option value="efectivo">Efectivo</option>
                      <option value="transferencia">Transferencia</option>
                      <option value="tarjeta">Tarjeta</option>
                      <option value="otro">Otro</option>
                    </select>
                  </label>
                  <label>Importe<input v-model="movimientoForm.importe" type="number" min="0" step="0.01" required /></label>
                  <label>Descripcion<input v-model="movimientoForm.descripcion" required /></label>
                </div>
              </section>
              <footer class="modal-actions">
                <button class="secondary-button" type="button" @click="closeMovimientoModal">Cancelar</button>
                <button class="primary-button modal-submit" :disabled="loading" type="submit">Guardar movimiento</button>
              </footer>
            </form>
          </div>
        </Teleport>

        <Teleport to="body">
          <div v-if="showCerrarCajaModal" class="modal-backdrop" @click.self="showCerrarCajaModal = false">
            <form class="modal-card compact-modal" @submit.prevent="cerrarCaja">
              <header class="modal-head">
                <div>
                  <p class="eyebrow">Cierre de caja</p>
                  <h2>Cerrar caja del dia</h2>
                  <span>Total esperado: $ {{ formatMoney(cajaTotales.total) }}</span>
                </div>
                <button class="icon-button" type="button" aria-label="Cerrar" @click="showCerrarCajaModal = false">×</button>
              </header>
              <section class="modal-section">
                <div class="modal-grid">
                  <label>Total contado<input v-model="cierreForm.total_contado" type="number" step="0.01" required /></label>
                </div>
              </section>
              <footer class="modal-actions">
                <button class="secondary-button" type="button" @click="showCerrarCajaModal = false">Cancelar</button>
                <button class="primary-button modal-submit" :disabled="loading" type="submit">Confirmar cierre</button>
              </footer>
            </form>
          </div>
        </Teleport>
      </section>
    </template>
  </main>
</template>
