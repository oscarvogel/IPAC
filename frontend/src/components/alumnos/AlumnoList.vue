<template>
  <section class="students-list-panel border-border bg-surface">
    <header class="students-panel-head">
      <div>
        <p class="eyebrow">Base académica</p>
        <h2>Alumnos</h2>
        <p>{{ sortedAlumnos.length }} {{ studentCountLabel }}</p>
      </div>
      <span class="students-list-count" aria-hidden="true">
        <UserGroupIcon />
        {{ sortedAlumnos.length }}
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
        </span>

        <ChevronRightIcon class="students-row-chevron" aria-hidden="true" />
      </button>

      <div v-if="!sortedAlumnos.length" class="students-empty-state">
        <span><UserGroupIcon aria-hidden="true" /></span>
        <strong>No encontramos alumnos</strong>
        <p>Probá cambiando la búsqueda o los filtros seleccionados.</p>
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

const studentCountLabel = computed(() =>
  sortedAlumnos.value.length === 1 ? 'alumno visible' : 'alumnos visibles',
)

function statusIcon(status) {
  return status === 'activo' ? CheckCircleIcon : PauseCircleIcon
}

function avatarInitials(alumno) {
  const name = (alumno.nombre || '').trim()
  const surname = (alumno.apellido || '').trim()
  return `${name.slice(0, 1)}${surname.slice(0, 1)}`.toUpperCase() || '?'
}
</script>
