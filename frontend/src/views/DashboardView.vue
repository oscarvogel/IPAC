<template>
  <section class="dashboard-screen">
    <div class="stats-grid">
      <article v-for="stat in stats" :key="stat.label" class="stat-card">
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
        <small>{{ stat.detail }}</small>
      </article>
    </div>

    <div class="dashboard-grid">
      <div class="panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Caja del dia</p>
            <h2>{{ cajaTitle }}</h2>
            <span v-if="cajaHoy">{{ cajaHoy.fecha }} · {{ cajaHoy.estado }}</span>
          </div>
        </div>
        <div class="dashboard-caja-body">
          <div>
            <span>Total esperado</span>
            <strong>$ {{ formatMoney(cajaTotalEsperado, { fractionDigits: 2 }) }}</strong>
          </div>
          <div>
            <span>Movimientos</span>
            <strong>{{ cajaMovimientos.length }}</strong>
          </div>
          <router-link to="/caja" class="primary-button">Ir a caja</router-link>
        </div>
      </div>

      <div class="panel table-card">
        <div class="panel-head">
          <div>
            <h2>Ultimos pagos</h2>
            <p>{{ ultimosPagos.length }} del mes en curso</p>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Recibo</th>
              <th>Fecha</th>
              <th>Alumno</th>
              <th>Medio</th>
              <th>Importe</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pago in ultimosPagos" :key="pago.id">
              <td>{{ pago.numero_recibo || '—' }}</td>
              <td>{{ formatDate(pago.fecha) }}</td>
              <td>{{ pago.alumno_nombre || '—' }}</td>
              <td><span class="table-badge">{{ pago.medio }}</span></td>
              <td>$ {{ formatMoney(pago.importe, { fractionDigits: 2 }) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="!ultimosPagos.length" class="empty-state flat">
          Todavia no hay pagos en el mes.
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { useCaja } from '@/composables/useCaja'
import { useCatalogos } from '@/composables/useCatalogos'
import { apiRequest } from '@/lib/api'
import { formatDate, formatMoney } from '@/lib/formatters'

const auth = useAuth()
const caja = useCaja()
const { sucursales, loadCatalogos } = useCatalogos()

const alumnosCount = ref(0)
const pagosMes = ref([])
const ultimosPagos = computed(() => pagosMes.value.slice(0, 5))
const totalCobradoMes = computed(() =>
  pagosMes.value.reduce((sum, p) => sum + Number(p.importe || 0), 0),
)

const { cajaHoy, cajaMovimientos, loadCajaHoy } = caja
const cajaTotalEsperado = computed(() =>
  cajaMovimientos.value.reduce((acc, m) => {
    const amount = Number(m.importe || 0)
    const signed = ['egreso', 'retiro', 'pase'].includes(m.tipo) ? -amount : amount
    return acc + signed
  }, 0),
)

const cajaTitle = computed(() => {
  if (!cajaHoy.value) return 'Sin caja abierta'
  return cajaHoy.value.sucursal_nombre || auth.user?.perfil?.sucursal?.nombre || 'Caja'
})

onMounted(async () => {
  await loadCatalogos()
  await Promise.all([cargarResumen(), loadCajaHoy()])
})

async function cargarResumen() {
  const hoy = new Date()
  const primero = new Date(hoy.getFullYear(), hoy.getMonth(), 1)
  const iso = (d) => d.toISOString().slice(0, 10)
  const [alumnos, pagos] = await Promise.all([
    apiRequest('/alumnos/'),
    apiRequest('/pagos/', {
      query: { desde: iso(primero), hasta: iso(hoy) },
    }),
  ])
  alumnosCount.value = alumnos.count ?? alumnos.results?.length ?? 0
  pagosMes.value = pagos.results || []
}

const stats = computed(() => [
  { label: 'Alumnos', value: alumnosCount.value, detail: 'base cargada' },
  { label: 'Sucursales', value: sucursales.value.length, detail: 'Posadas y Eldorado' },
  {
    label: 'Cobrado del mes',
    value: `$ ${formatMoney(totalCobradoMes.value, { fractionDigits: 2 })}`,
    detail: `${pagosMes.value.length} pagos`,
  },
  {
    label: 'Pagos del mes',
    value: pagosMes.value.length,
    detail: 'filtrados por periodo actual',
  },
])
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

.dashboard-caja-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 0;
}

.dashboard-caja-body > div {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  border-bottom: 1px solid #f0f0f4;
  padding-bottom: 8px;
}

.dashboard-caja-body > div:last-of-type {
  border-bottom: none;
}

.dashboard-caja-body strong {
  font-size: 1.1rem;
  color: #2a2a35;
}

.dashboard-caja-body a {
  align-self: flex-start;
  text-decoration: none;
}
</style>
