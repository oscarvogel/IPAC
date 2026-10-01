<template>
  <section class="reports-filter-card border-border bg-surface">
    <div class="reports-filter-heading">
      <span class="reports-filter-icon">
        <ChartBarSquareIcon aria-hidden="true" />
      </span>
      <div>
        <p class="eyebrow">Análisis financiero</p>
        <h2>{{ showPeriod ? 'Período del reporte' : 'Alcance del reporte' }}</h2>
        <p>{{ showExport ? 'Definí el alcance del informe y exportá sus resultados.' : 'Definí el período y revisá los indicadores operativos.' }}</p>
      </div>
    </div>

    <div class="report-filter-shortcuts">
      <button v-if="showPeriod" type="button" :disabled="loading" @click="shortcut('hoy')">Hoy</button>
      <button v-if="showPeriod" type="button" :disabled="loading" @click="shortcut('mes')">Este mes</button>
      <button type="button" :disabled="loading" @click="clear">Limpiar filtros</button>
    </div>

    <div class="reports-filter-controls">
      <label v-if="showPeriod" class="reports-filter-field reports-date-field">
        <span><CalendarDaysIcon aria-hidden="true" /> Desde</span>
        <input v-model="local.desde" type="date" />
      </label>
      <label v-if="showPeriod" class="reports-filter-field reports-date-field">
        <span><CalendarDaysIcon aria-hidden="true" /> Hasta</span>
        <input v-model="local.hasta" type="date" />
      </label>
      <label class="reports-filter-field reports-select-field">
        <span><BuildingStorefrontIcon aria-hidden="true" /> Sucursal</span>
        <span class="reports-select-control">
          <select v-model="local.sucursal">
            <option value="">Todas las sucursales</option>
            <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
              {{ sucursal.nombre }}
            </option>
          </select>
          <ChevronDownIcon aria-hidden="true" />
        </span>
      </label>
      <label v-if="showUser" class="reports-filter-field reports-select-field">
        <span><UserIcon aria-hidden="true" /> Cajero</span>
        <span class="reports-select-control">
          <select v-model="local.usuario">
            <option value="">Todos los cajeros</option>
            <option v-for="usuario in usuarios" :key="usuario.id" :value="usuario.id">
              {{ usuario.nombre }}
            </option>
          </select>
          <ChevronDownIcon aria-hidden="true" />
        </span>
      </label>
      <label v-if="showMedium" class="reports-filter-field reports-select-field">
        <span><CreditCardIcon aria-hidden="true" /> Medio</span>
        <span class="reports-select-control">
          <select v-model="local.medio">
            <option value="">Todos los medios</option>
            <option value="efectivo">Efectivo</option>
            <option value="transferencia">Transferencia</option>
            <option value="mercado_pago">Mercado Pago</option>
            <option value="tarjeta">Tarjeta</option>
            <option value="otro">Otro</option>
          </select>
          <ChevronDownIcon aria-hidden="true" />
        </span>
      </label>
      <div class="reports-filter-actions">
        <button
          class="reports-apply-action bg-primary hover:bg-primary-hover"
          type="button"
          :disabled="loading"
          @click="aplicar"
        >
          <ArrowPathIcon v-if="loading" class="is-spinning" aria-hidden="true" />
          <FunnelIcon v-else aria-hidden="true" />
          <span>{{ loading ? 'Cargando' : 'Aplicar' }}</span>
        </button>
        <button
          v-if="showExport"
          class="reports-export-action"
          type="button"
          :disabled="loading"
          @click="exportar"
        >
          <ArrowDownTrayIcon aria-hidden="true" />
          <span>{{ exportLabel }}</span>
        </button>
      </div>
    </div>
    <p v-if="pending" class="filter-pending" role="status">Cambios pendientes: pulsá Aplicar para actualizar los resultados.</p>
    <p v-if="validationError" role="alert">{{ validationError }}</p>
    <div class="report-filter-chips" aria-label="Filtros de los resultados mostrados">
      <span>Consulta aplicada:</span>
      <button v-if="showPeriod && (filtros.desde || filtros.hasta)" type="button" :disabled="loading" @click="remove('periodo')">{{ formatDate(filtros.desde) }} a {{ formatDate(filtros.hasta) }} · Quitar período</button>
      <span v-else-if="showPeriod">Todo el período</span>
      <span v-else>Listado actual de alumnos</span>
      <button v-if="filtros.sucursal" type="button" :disabled="loading" @click="remove('sucursal')">Sucursal: {{ sucursales.find(item => String(item.id) === String(filtros.sucursal))?.nombre || 'Selección guardada' }} · Quitar</button>
      <button v-if="showUser && filtros.usuario" type="button" :disabled="loading" @click="remove('usuario')">Cajero: {{ usuarios.find(item => String(item.id) === String(filtros.usuario))?.nombre || 'Selección guardada' }} · Quitar</button>
      <button v-if="showMedium && filtros.medio" type="button" :disabled="loading" @click="remove('medio')">Medio: {{ medioLabel(filtros.medio) }} · Quitar</button>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { periodoFechas } from '@/lib/consultas'
import { formatDate } from '@/lib/formatters'
import {
  ArrowDownTrayIcon,
  ArrowPathIcon,
  BuildingStorefrontIcon,
  CalendarDaysIcon,
  ChartBarSquareIcon,
  ChevronDownIcon,
  CreditCardIcon,
  FunnelIcon,
  UserIcon,
} from '@heroicons/vue/24/outline'

const props = defineProps({
  filtros: { type: Object, required: true },
  sucursales: { type: Array, required: true },
  loading: { type: Boolean, default: false },
  exportLabel: { type: String, default: 'Exportar Excel' },
  usuarios: { type: Array, default: () => [] },
  showUser: { type: Boolean, default: false },
  showMedium: { type: Boolean, default: true },
  showExport: { type: Boolean, default: true },
  showPeriod: { type: Boolean, default: true },
  periodo: { type: String, default: 'mes' },
})

const emit = defineEmits(['aplicar', 'exportar'])

const local = reactive({ ...props.filtros })
const validationError = ref('')
const pending = computed(() => [...(props.showPeriod ? ['desde', 'hasta'] : []), 'sucursal', ...(props.showUser ? ['usuario'] : []), ...(props.showMedium ? ['medio'] : [])].some(key => String(local[key] || '') !== String(props.filtros[key] || '')))
function medioLabel(value) { return { efectivo:'Efectivo', transferencia:'Transferencia', mercado_pago:'Mercado Pago', tarjeta:'Tarjeta', otro:'Otro' }[value] || value }
function direct(filters, periodo) { Object.assign(local, filters); emit('aplicar', filters, periodo) }
function shortcut(periodo) { direct({ ...props.filtros, ...periodoFechas(periodo) }, periodo) }
function clear() { direct({ desde: '', hasta: '', sucursal: '', medio: '', usuario: '' }, 'todos') }
function remove(key) {
  const next = { ...props.filtros }
  if (key === 'periodo') { next.desde = ''; next.hasta = '' } else next[key] = ''
  if (key === 'sucursal') next.usuario = ''
  direct(next, key === 'periodo' ? 'todos' : props.periodo)
}

watch(
  () => props.filtros,
  (nuevo) => {
    Object.assign(local, nuevo)
  },
  { deep: true },
)

function aplicar() {
  validationError.value = ''
  if (Boolean(local.desde) !== Boolean(local.hasta) || (local.desde && local.desde > local.hasta)) { validationError.value = 'Indicá Desde y Hasta con un rango válido, o dejá ambas fechas vacías.'; return }
  const datesChanged = local.desde !== props.filtros.desde || local.hasta !== props.filtros.hasta
  emit('aplicar', { ...local, usuario: props.showUser ? local.usuario : '', medio: props.showMedium ? local.medio : '' }, datesChanged ? (local.desde ? 'personalizado' : 'todos') : props.periodo)
}

function exportar() {
  emit('exportar')
}
</script>

<style scoped>
.report-filter-shortcuts,.report-filter-chips{display:flex;align-items:center;flex-wrap:wrap;gap:.5rem;margin:.8rem 0}.report-filter-shortcuts button,.report-filter-chips button{min-height:44px;border:1px solid var(--border);border-radius:.6rem;padding:.4rem .7rem;background:var(--surface);color:var(--primary);font-weight:700;white-space:normal}.report-filter-chips{font-size:.85rem;color:var(--text-secondary)}.filter-pending{color:var(--warning);font-weight:700}.reports-filter-card [role=alert]{color:var(--danger)}.report-filter-shortcuts :focus-visible,.report-filter-chips :focus-visible{outline:3px solid var(--primary);outline-offset:2px}
</style>
