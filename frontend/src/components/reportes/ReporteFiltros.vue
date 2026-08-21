<template>
  <section class="reports-filter-card border-border bg-surface">
    <div class="reports-filter-heading">
      <span class="reports-filter-icon">
        <ChartBarSquareIcon aria-hidden="true" />
      </span>
      <div>
        <p class="eyebrow">Análisis financiero</p>
        <h2>Período del reporte</h2>
        <p>Definí el alcance del informe y exportá sus resultados.</p>
      </div>
    </div>

    <div class="reports-filter-controls">
      <label class="reports-filter-field reports-date-field">
        <span><CalendarDaysIcon aria-hidden="true" /> Desde</span>
        <input v-model="local.desde" type="date" />
      </label>
      <label class="reports-filter-field reports-date-field">
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
      <label class="reports-filter-field reports-select-field">
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
  </section>
</template>

<script setup>
import { reactive, watch } from 'vue'
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
})

const emit = defineEmits(['update:filtros', 'aplicar', 'exportar'])

const local = reactive({ ...props.filtros })

watch(
  () => props.filtros,
  (nuevo) => {
    Object.assign(local, nuevo)
  },
  { deep: true },
)

function syncFilters() {
  emit('update:filtros', { ...local })
}

function aplicar() {
  syncFilters()
  emit('aplicar')
}

function exportar() {
  syncFilters()
  emit('exportar')
}
</script>
