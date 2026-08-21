<template>
  <section class="cash-operation-hero border-border bg-surface">
    <div class="cash-operation-heading">
      <span class="cash-operation-icon">
        <WalletIcon aria-hidden="true" />
      </span>
      <div>
        <p class="eyebrow">Tesorería diaria</p>
        <h2>{{ sucursalLabel }}</h2>
        <div class="cash-operation-meta">
          <span>
            <CalendarDaysIcon aria-hidden="true" />
            {{ formattedDate }}
          </span>
          <span :class="['cash-status-badge', cajaStatus]">
            <span class="cash-status-dot" aria-hidden="true" />
            {{ statusLabel }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="isClosed" class="cash-closed-summary" role="status">
      <strong>Caja cerrada</strong>
      <span>{{ closedAtLabel }} · {{ cajaHoy?.usuario_nombre }}</span>
      <small>La jornada quedó bloqueada para nuevas operaciones.</small>
    </div>

    <div class="cash-operation-actions">
      <button
        type="button"
        class="cash-action cash-action-muted"
        :disabled="!cajaHoy"
        @click="$emit('print')"
      >
        <PrinterIcon aria-hidden="true" />
        <span>{{ isClosed ? 'Imprimir cierre' : 'Imprimir' }}</span>
      </button>
      <button
        v-if="!isClosed"
        type="button"
        class="cash-action cash-action-primary"
        :disabled="!puedeMover"
        @click="$emit('movimiento', 'ingreso')"
      >
        <PlusCircleIcon aria-hidden="true" />
        <span>Ingreso</span>
      </button>
      <button
        v-if="!isClosed"
        type="button"
        class="cash-action"
        :disabled="!puedeMover"
        @click="$emit('movimiento', 'egreso')"
      >
        <MinusCircleIcon aria-hidden="true" />
        <span>Egreso</span>
      </button>
      <button
        v-if="!isClosed"
        type="button"
        class="cash-action cash-action-warning"
        :disabled="!puedeMover"
        @click="$emit('movimiento', 'retiro')"
      >
        <BanknotesIcon aria-hidden="true" />
        <span>Retiro</span>
      </button>
      <button
        v-if="!isClosed"
        type="button"
        class="cash-action cash-action-danger"
        :disabled="!puedeMover"
        @click="$emit('cerrar')"
      >
        <LockClosedIcon aria-hidden="true" />
        <span>Cerrar caja</span>
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import {
  BanknotesIcon,
  CalendarDaysIcon,
  LockClosedIcon,
  MinusCircleIcon,
  PlusCircleIcon,
  PrinterIcon,
  WalletIcon,
} from '@heroicons/vue/24/outline'
import { formatDate } from '@/lib/formatters'

const props = defineProps({
  cajaHoy: { type: Object, default: null },
  fallbackSucursal: { type: String, default: '' },
  puedeMover: { type: Boolean, default: false },
})

defineEmits(['print', 'movimiento', 'cerrar'])

const sucursalLabel = computed(
  () => props.cajaHoy?.sucursal_nombre || props.fallbackSucursal || 'Caja sin asignar',
)

const cajaStatus = computed(() => props.cajaHoy?.estado || 'sin-caja')
const isClosed = computed(() => props.cajaHoy?.estado === 'cerrada')

const statusLabel = computed(() => {
  if (!props.cajaHoy) return 'Sin caja abierta'
  if (props.cajaHoy.estado === 'abierta') return 'Abierta'
  if (props.cajaHoy.estado === 'cerrada') return 'Cerrada'
  return props.cajaHoy.estado || 'Sin estado'
})

const formattedDate = computed(() =>
  props.cajaHoy?.fecha ? formatDate(props.cajaHoy.fecha) : 'Sin actividad para hoy',
)

const closedAtLabel = computed(() => {
  if (!props.cajaHoy?.cerrada_en) return 'Cierre registrado'
  return new Intl.DateTimeFormat('es-AR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(props.cajaHoy.cerrada_en))
})
</script>
