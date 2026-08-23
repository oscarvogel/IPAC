<template>
  <section class="branches-directory border-border bg-surface">
    <header class="branches-directory-head">
      <div class="branches-directory-title">
        <span class="branches-directory-icon">
          <MapIcon aria-hidden="true" />
        </span>
        <div>
          <p class="eyebrow">Sedes del instituto</p>
          <h2>Sucursales</h2>
          <p>Accesos operativos y oferta académica por sede.</p>
        </div>
      </div>
      <span class="branches-directory-count">
        {{ sortedSucursales.length }} {{ sortedSucursales.length === 1 ? 'sede' : 'sedes' }}
      </span>
    </header>

    <div v-if="sortedSucursales.length" class="branches-card-grid">
      <article
        v-for="sucursal in sortedSucursales"
        :key="sucursal.id"
        class="branch-card"
        :class="{ inactive: !sucursal.activa }"
      >
        <header class="branch-card-head">
          <span class="branch-building-icon">
            <BuildingOffice2Icon aria-hidden="true" />
          </span>
          <span :class="['branch-status', sucursal.activa ? 'active' : 'inactive']">
            <component :is="sucursal.activa ? CheckCircleIcon : PauseCircleIcon" aria-hidden="true" />
            {{ sucursal.activa ? 'Activa' : 'Inactiva' }}
          </span>
        </header>

        <div class="branch-card-copy">
          <span class="branch-code">{{ sucursal.codigo || 'SIN CÓDIGO' }}</span>
          <h3>{{ sucursal.nombre }}</h3>
          <p>{{ sucursal.activa ? 'Sede habilitada para operaciones administrativas.' : 'Sede temporalmente fuera de operación.' }}</p>
        </div>

        <div class="branch-card-meta">
          <span>
            <AcademicCapIcon aria-hidden="true" />
            <span>
              <small>Oferta académica</small>
              <strong>{{ careerCount(sucursal.id) }} {{ careerCount(sucursal.id) === 1 ? 'carrera' : 'carreras' }}</strong>
            </span>
          </span>
          <span>
            <IdentificationIcon aria-hidden="true" />
            <span>
              <small>Código interno</small>
              <strong>{{ sucursal.codigo || 'No asignado' }}</strong>
            </span>
          </span>
        </div>

        <footer class="branch-card-actions">
          <button v-if="canEdit" type="button" @click="$emit('edit', sucursal)">
            <PencilSquareIcon aria-hidden="true" />
            <span>Editar sede</span>
          </button>
          <button
            v-if="canDeactivate && sucursal.activa"
            type="button"
            class="deactivate"
            @click="$emit('deactivate', sucursal)"
          >
            <NoSymbolIcon aria-hidden="true" />
            <span>Desactivar</span>
          </button>
        </footer>
      </article>
    </div>

    <div v-else class="branches-empty-state">
      <span><BuildingOffice2Icon aria-hidden="true" /></span>
      <strong>No hay sucursales cargadas</strong>
      <p>Creá la primera sede para comenzar a configurar la operación del CRM.</p>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import {
  AcademicCapIcon,
  BuildingOffice2Icon,
  CheckCircleIcon,
  IdentificationIcon,
  MapIcon,
  NoSymbolIcon,
  PauseCircleIcon,
  PencilSquareIcon,
} from '@heroicons/vue/24/outline'

const props = defineProps({
  sucursales: { type: Array, required: true },
  carreras: { type: Array, default: () => [] },
  canEdit: { type: Boolean, default: true },
  canDeactivate: { type: Boolean, default: true },
})

defineEmits(['edit', 'deactivate'])

const sortedSucursales = computed(() =>
  [...props.sucursales].sort((a, b) => {
    if (a.activa !== b.activa) return a.activa ? -1 : 1
    return (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' })
  }),
)

function careerCount(sucursalId) {
  return props.carreras.filter(
    (carrera) => String(carrera.sucursal) === String(sucursalId),
  ).length
}
</script>
