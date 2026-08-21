<template>
  <section class="students-list-panel border-border bg-surface">
    <header class="students-panel-head">
      <div>
        <p class="eyebrow">Base académica</p>
        <h2>Alumnos</h2>
        <p>{{ displayedCount }} {{ studentCountLabel }}</p>
      </div>
      <span class="students-list-count" aria-hidden="true">
        <UserGroupIcon />
        {{ displayedCount }}
      </span>
    </header>

    <div class="students-list">
      <button
        v-for="alumno in sortedAlumnos"
        :key="alumno.id"
        :class="{ selected: selectedAlumno?.id === alumno.id }"
        :aria-pressed="selectedAlumno?.id === alumno.id"
        class="students-row"
        type="button"
        @click="$emit('select', alumno)"
      >
        <span class="students-avatar">{{ avatarInitials(alumno) }}</span>

        <span class="students-row-copy">
          <strong>{{ alumno.apellido }}, {{ alumno.nombre }}</strong>
          <small>
            <IdentificationIcon aria-hidden="true" />
            {{ alumno.legajo || 'Sin legajo' }}
            <span aria-hidden="true">•</span>
            {{ alumno.carrera_nombre || 'Sin carrera asignada' }}
          </small>
        </span>

        <span class="students-row-location">
          <small>
            <MapPinIcon aria-hidden="true" />
            {{ alumno.sucursal_nombre || 'Sin sucursal' }}
          </small>
          <em :class="['students-status', alumno.estado]">
            <component :is="statusIcon(alumno.estado)" aria-hidden="true" />
            {{ alumno.estado || 'sin estado' }}
          </em>
          <span v-if="Number(alumno.deuda_total) > 0" class="student-financial-badge debt">
            Debe {{ formatCurrency(alumno.deuda_total) }}
          </span>
          <span v-else-if="Number(alumno.saldo_a_favor) > 0" class="student-financial-badge credit">
            A favor {{ formatCurrency(alumno.saldo_a_favor) }}
          </span>
          <span v-else class="student-financial-badge clear">Al día</span>
        </span>

        <ChevronRightIcon class="students-row-chevron" aria-hidden="true" />
      </button>

      <div v-if="!sortedAlumnos.length" class="students-empty-state">
        <span><UserGroupIcon aria-hidden="true" /></span>
        <strong>{{ filtered ? 'No encontramos alumnos' : 'Todavía no hay alumnos cargados' }}</strong>
        <p>{{ filtered ? 'Probá cambiando la búsqueda o los filtros seleccionados.' : 'Creá el primer legajo para comenzar a gestionar alumnos.' }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import {
  CheckCircleIcon,
  ChevronRightIcon,
  IdentificationIcon,
  MapPinIcon,
  PauseCircleIcon,
  UserGroupIcon,
} from '@heroicons/vue/24/outline'

const props = defineProps({
  alumnos: { type: Array, required: true },
  selectedAlumno: { type: Object, default: null },
  filtered: { type: Boolean, default: false },
  totalCount: { type: Number, default: null },
})

defineEmits(['select'])

const sortedAlumnos = computed(() =>
  [...props.alumnos].sort((a, b) =>
    `${a.apellido || ''} ${a.nombre || ''}`.localeCompare(
      `${b.apellido || ''} ${b.nombre || ''}`,
      'es',
      { sensitivity: 'base' },
    ),
  ),
)

const displayedCount = computed(() => props.totalCount ?? sortedAlumnos.value.length)

const studentCountLabel = computed(() =>
  displayedCount.value === 1 ? 'alumno encontrado' : 'alumnos encontrados',
)

function statusIcon(status) {
  return status === 'activo' ? CheckCircleIcon : PauseCircleIcon
}

function avatarInitials(alumno) {
  const name = (alumno.nombre || '').trim()
  const surname = (alumno.apellido || '').trim()
  return `${name.slice(0, 1)}${surname.slice(0, 1)}`.toUpperCase() || '?'
}

function formatCurrency(value) {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    maximumFractionDigits: 0,
  }).format(Number(value || 0))
}
</script>
