<template>
  <section class="concepts-list-card border-border bg-surface">
    <header class="concepts-list-head">
      <div class="concepts-list-title">
        <span class="concepts-list-icon">
          <RectangleStackIcon aria-hidden="true" />
        </span>
        <div>
          <p class="eyebrow">Configuración de cobros</p>
          <h2>Conceptos cobrables</h2>
          <p>Valores vigentes por sucursal y carrera.</p>
        </div>
      </div>
      <span class="concepts-list-count">
        {{ sortedConceptos.length }} {{ sortedConceptos.length === 1 ? 'concepto' : 'conceptos' }}
      </span>
    </header>

    <div class="concepts-table-wrap">
      <table class="concepts-table">
        <thead>
          <tr>
            <th>Concepto</th>
            <th>Tipo</th>
            <th>Importe</th>
            <th>Sucursal</th>
            <th>Carrera</th>
            <th>Estado</th>
            <th><span class="sr-only">Acciones</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="concepto in sortedConceptos" :key="concepto.id">
            <td>
              <div class="concepts-name-cell">
                <span :class="['concepts-type-icon', `type-${concepto.tipo || 'otro'}`]">
                  <component :is="typeIcon(concepto.tipo)" aria-hidden="true" />
                </span>
                <span>
                  <strong>{{ concepto.nombre }}</strong>
                  <small>{{ concepto.carrera_nombre || 'Aplicación general' }}</small>
                </span>
              </div>
            </td>
            <td>
              <span :class="['concepts-type-badge', `type-${concepto.tipo || 'otro'}`]">
                {{ typeLabel(concepto.tipo) }}
              </span>
            </td>
            <td class="concepts-amount">
              $ {{ formatMoney(concepto.importe, { fractionDigits: 2 }) }}
            </td>
            <td>
              <span class="concepts-location">
                <BuildingStorefrontIcon aria-hidden="true" />
                {{ concepto.sucursal_nombre || 'Sin sucursal' }}
              </span>
            </td>
            <td class="concepts-career">{{ concepto.carrera_nombre || 'Todas las carreras' }}</td>
            <td>
              <span :class="['concepts-status', concepto.activo ? 'active' : 'inactive']">
                <component :is="concepto.activo ? CheckCircleIcon : PauseCircleIcon" aria-hidden="true" />
                {{ concepto.activo ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td>
              <div class="concepts-row-actions">
                <button
                  type="button"
                  title="Editar concepto"
                  aria-label="Editar concepto"
                  @click="$emit('edit', concepto)"
                >
                  <PencilSquareIcon aria-hidden="true" />
                </button>
                <button
                  v-if="concepto.activo"
                  type="button"
                  class="deactivate"
                  title="Desactivar concepto"
                  aria-label="Desactivar concepto"
                  @click="$emit('deactivate', concepto)"
                >
                  <NoSymbolIcon aria-hidden="true" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="sortedConceptos.length" class="mobile-record-list concepts-mobile-list" role="list">
        <article
          v-for="concepto in sortedConceptos"
          :key="`mobile-${concepto.id}`"
          class="mobile-record-card concept-mobile-card"
          role="listitem"
        >
          <header class="mobile-record-head">
            <span :class="['concepts-type-icon', `type-${concepto.tipo || 'otro'}`]">
              <component :is="typeIcon(concepto.tipo)" aria-hidden="true" />
            </span>
            <span class="mobile-record-title">
              <strong>{{ concepto.nombre }}</strong>
              <small>{{ typeLabel(concepto.tipo) }}</small>
            </span>
            <MobileActionMenu :label="`Acciones para ${concepto.nombre}`">
              <button type="button" role="menuitem" @click="$emit('edit', concepto)">
                <PencilSquareIcon aria-hidden="true" />
                <span>Editar concepto</span>
              </button>
              <button
                v-if="concepto.activo"
                type="button"
                class="danger"
                role="menuitem"
                @click="$emit('deactivate', concepto)"
              >
                <NoSymbolIcon aria-hidden="true" />
                <span>Desactivar</span>
              </button>
            </MobileActionMenu>
          </header>

          <strong class="mobile-record-amount">
            $ {{ formatMoney(concepto.importe, { fractionDigits: 2 }) }}
          </strong>

          <dl class="mobile-record-meta">
            <div>
              <dt>Sucursal</dt>
              <dd><BuildingStorefrontIcon aria-hidden="true" />{{ concepto.sucursal_nombre || 'Sin sucursal' }}</dd>
            </div>
            <div>
              <dt>Carrera</dt>
              <dd><AcademicCapIcon aria-hidden="true" />{{ concepto.carrera_nombre || 'Todas las carreras' }}</dd>
            </div>
          </dl>

          <footer class="mobile-record-footer">
            <span :class="['concepts-status', concepto.activo ? 'active' : 'inactive']">
              <component :is="concepto.activo ? CheckCircleIcon : PauseCircleIcon" aria-hidden="true" />
              {{ concepto.activo ? 'Activo' : 'Inactivo' }}
            </span>
          </footer>
        </article>
      </div>

      <div v-if="!sortedConceptos.length" class="concepts-empty-state">
        <span><TagIcon aria-hidden="true" /></span>
        <strong>{{ filtered ? 'No encontramos conceptos' : 'Todavía no hay conceptos cargados' }}</strong>
        <p>{{ filtered ? 'Probá cambiando la búsqueda o los filtros seleccionados.' : 'Creá el primer concepto para configurar los aranceles.' }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import {
  AcademicCapIcon,
  BookOpenIcon,
  BuildingStorefrontIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  NoSymbolIcon,
  PauseCircleIcon,
  PencilSquareIcon,
  RectangleStackIcon,
  TagIcon,
} from '@heroicons/vue/24/outline'
import { formatMoney } from '@/lib/formatters'
import MobileActionMenu from '@/components/ui/MobileActionMenu.vue'

const props = defineProps({
  conceptos: { type: Array, required: true },
  filtered: { type: Boolean, default: false },
})

defineEmits(['edit', 'deactivate'])

const sortedConceptos = computed(() =>
  [...props.conceptos].sort((a, b) =>
    (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' }),
  ),
)

function typeLabel(type) {
  const labels = {
    matricula: 'Matrícula',
    cuota: 'Cuota',
    material: 'Material',
    otro: 'Otro',
  }
  return labels[type] || type || 'Otro'
}

function typeIcon(type) {
  const icons = {
    matricula: AcademicCapIcon,
    cuota: DocumentTextIcon,
    material: BookOpenIcon,
    otro: TagIcon,
  }
  return icons[type] || TagIcon
}
</script>
