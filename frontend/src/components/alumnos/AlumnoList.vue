<template>
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
        @click="$emit('select', alumno)"
      >
        <span class="avatar">{{ avatarInitials(alumno) }}</span>
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
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  alumnos: { type: Array, required: true },
  selectedAlumno: { type: Object, default: null },
  searchQuery: { type: String, default: '' },
  sucursalFilter: { type: [String, Number], default: 'todas' },
})

defineEmits(['select'])

const filteredAlumnos = computed(() => {
  const query = props.searchQuery.trim().toLowerCase()
  return props.alumnos.filter((alumno) => {
    const matchesSucursal =
      props.sucursalFilter === 'todas' ||
      String(alumno.sucursal) === String(props.sucursalFilter)
    const text = [
      alumno.legajo,
      alumno.nombre,
      alumno.apellido,
      alumno.dni,
      alumno.email,
      alumno.sucursal_nombre,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    return matchesSucursal && (!query || text.includes(query))
  })
})

function avatarInitials(alumno) {
  const n = (alumno.nombre || '').trim()
  const a = (alumno.apellido || '').trim()
  return `${n.slice(0, 1)}${a.slice(0, 1)}`.toUpperCase() || '?'
}
</script>
