<template>
  <section class="careers-list-card border-border bg-surface">
    <header class="careers-list-head">
      <div class="careers-list-title">
        <span class="careers-list-icon">
          <AcademicCapIcon aria-hidden="true" />
        </span>
        <div>
          <p class="eyebrow">Trayectoria académica</p>
          <h2>Carreras y cursos</h2>
          <p>Planes de estudio y valores de cuota por sucursal.</p>
        </div>
      </div>
      <span class="careers-list-count">
        {{ sortedCarreras.length }} {{ sortedCarreras.length === 1 ? 'carrera' : 'carreras' }}
      </span>
    </header>

    <div class="careers-table-wrap">
      <table class="careers-table">
        <thead>
          <tr>
            <th>Carrera o curso</th>
            <th>Tipo</th>
            <th>Plan</th>
            <th>Cuota total</th>
            <th>Desglose de la cuota</th>
            <th>Estado</th>
            <th><span class="sr-only">Acciones</span></th>
          </tr>
        </thead>
        <MotionList tag="tbody" data-motion-list="carreras-desktop" :animate="animate">
          <tr v-for="carrera in paginatedCarreras" :key="carrera.id" data-motion-item>
            <td>
              <div class="careers-name-cell">
                <span :class="['careers-type-icon', `type-${carrera.tipo || 'carrera'}`]">
                  <component :is="typeIcon(carrera.tipo)" aria-hidden="true" />
                </span>
                <span>
                  <strong>{{ carrera.nombre }}</strong>
                  <small>{{ carrera.sucursal_nombre || 'Sin sucursal' }}</small>
                </span>
              </div>
            </td>
            <td>
              <span :class="['careers-type-badge', `type-${carrera.tipo || 'carrera'}`]">
                {{ typeLabel(carrera.tipo) }}
              </span>
            </td>
            <td class="careers-plan">
              <span v-if="carrera.plan_cuotas">{{ carrera.plan_cuotas }} cuotas</span>
              <span v-else class="careers-muted">Sin definir</span>
            </td>
            <td class="careers-amount">
              <span v-if="carrera.cuota_total">
                $ {{ formatMoney(carrera.cuota_total, { fractionDigits: 2 }) }}
              </span>
              <span v-else class="careers-muted">Sin definir</span>
            </td>
            <td>
              <span v-if="tieneDesglose(carrera)" class="careers-split">
                <span>
                  <small>Programática</small>
                  <strong>$ {{ formatMoney(carrera.cuota_programatica, { fractionDigits: 2 }) }}</strong>
                </span>
                <span>
                  <small>Extraprogramática</small>
                  <strong>$ {{ formatMoney(carrera.cuota_extraprogramatica, { fractionDigits: 2 }) }}</strong>
                </span>
              </span>
              <span v-else class="careers-missing">
                <ExclamationTriangleIcon aria-hidden="true" />
                Sin desglose
              </span>
            </td>
            <td>
              <span :class="['careers-status', carrera.activa ? 'active' : 'inactive']">
                <component :is="carrera.activa ? CheckCircleIcon : PauseCircleIcon" aria-hidden="true" />
                {{ carrera.activa ? 'Activa' : 'Inactiva' }}
              </span>
            </td>
            <td>
              <div class="careers-row-actions">
                <button
                  v-if="canEdit"
                  type="button"
                  title="Editar carrera"
                  aria-label="Editar carrera"
                  @click="$emit('edit', carrera)"
                >
                  <PencilSquareIcon aria-hidden="true" />
                </button>
                <button
                  v-if="canDeactivate && carrera.activa"
                  type="button"
                  class="deactivate"
                  title="Desactivar carrera"
                  aria-label="Desactivar carrera"
                  @click="$emit('deactivate', carrera)"
                >
                  <NoSymbolIcon aria-hidden="true" />
                </button>
              </div>
            </td>
          </tr>
        </MotionList>
      </table>

      <MotionList
        v-if="sortedCarreras.length"
        class="mobile-record-list careers-mobile-list"
        data-motion-list="carreras-mobile"
        role="list"
        :animate="animate"
      >
        <article
          v-for="carrera in paginatedCarreras"
          :key="`mobile-${carrera.id}`"
          data-motion-item
          class="mobile-record-card careers-mobile-card"
          role="listitem"
        >
          <header class="mobile-record-head">
            <span :class="['careers-type-icon', `type-${carrera.tipo || 'carrera'}`]">
              <component :is="typeIcon(carrera.tipo)" aria-hidden="true" />
            </span>
            <span class="mobile-record-title">
              <strong>{{ carrera.nombre }}</strong>
              <small>{{ typeLabel(carrera.tipo) }}</small>
            </span>
            <MobileActionMenu :label="`Acciones para ${carrera.nombre}`">
              <button v-if="canEdit" type="button" role="menuitem" @click="$emit('edit', carrera)">
                <PencilSquareIcon aria-hidden="true" />
                <span>Editar carrera</span>
              </button>
              <button
                v-if="canDeactivate && carrera.activa"
                type="button"
                class="danger"
                role="menuitem"
                @click="$emit('deactivate', carrera)"
              >
                <NoSymbolIcon aria-hidden="true" />
                <span>Desactivar</span>
              </button>
            </MobileActionMenu>
          </header>

          <strong class="mobile-record-amount">
            <template v-if="carrera.cuota_total">
              $ {{ formatMoney(carrera.cuota_total, { fractionDigits: 2 }) }}
            </template>
            <template v-else>Cuota sin definir</template>
          </strong>

          <span v-if="tieneDesglose(carrera)" class="careers-split careers-split-mobile">
            <span>
              <small>Programática</small>
              <strong>$ {{ formatMoney(carrera.cuota_programatica, { fractionDigits: 2 }) }}</strong>
            </span>
            <span>
              <small>Extraprogramática</small>
              <strong>$ {{ formatMoney(carrera.cuota_extraprogramatica, { fractionDigits: 2 }) }}</strong>
            </span>
          </span>
          <span v-else class="careers-missing">
            <ExclamationTriangleIcon aria-hidden="true" />
            Sin desglose
          </span>

          <dl class="mobile-record-meta">
            <div>
              <dt>Sucursal</dt>
              <dd>
                <BuildingStorefrontIcon aria-hidden="true" />
                {{ carrera.sucursal_nombre || 'Sin sucursal' }}
              </dd>
            </div>
            <div>
              <dt>Plan</dt>
              <dd>
                <RectangleStackIcon aria-hidden="true" />
                {{ carrera.plan_cuotas ? `${carrera.plan_cuotas} cuotas` : 'Sin definir' }}
              </dd>
            </div>
          </dl>

          <footer class="mobile-record-footer">
            <span :class="['careers-status', carrera.activa ? 'active' : 'inactive']">
              <component :is="carrera.activa ? CheckCircleIcon : PauseCircleIcon" aria-hidden="true" />
              {{ carrera.activa ? 'Activa' : 'Inactiva' }}
            </span>
          </footer>
        </article>
      </MotionList>

      <nav
        v-if="sortedCarreras.length"
        class="catalog-pagination"
        aria-label="Paginación de carreras"
      >
        <label class="catalog-page-size">
          <span>Mostrar</span>
          <select v-model="pageSize" aria-label="Carreras por página">
            <option v-for="size in pageSizes" :key="size" :value="size">{{ size }}</option>
          </select>
        </label>
        <button type="button" :disabled="page <= 1" @click="goToPage(page - 1)">Anterior</button>
        <span aria-live="polite">
          Página {{ page }} de {{ totalPages }} · {{ sortedCarreras.length }} carreras
        </span>
        <button type="button" :disabled="page >= totalPages" @click="goToPage(page + 1)">Siguiente</button>
      </nav>

      <div v-if="!sortedCarreras.length" class="careers-empty-state">
        <span><AcademicCapIcon aria-hidden="true" /></span>
        <strong>{{ filtered ? 'No encontramos carreras' : 'Todavía no hay carreras cargadas' }}</strong>
        <p>
          {{
            filtered
              ? 'Probá cambiando la búsqueda o los filtros seleccionados.'
              : 'Crea la primera carrera para poder generar cuotas con desglose programático.'
          }}
        </p>
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
  ExclamationTriangleIcon,
  NoSymbolIcon,
  PauseCircleIcon,
  PencilSquareIcon,
  RectangleStackIcon,
} from '@heroicons/vue/24/outline'
import { formatMoney } from '@/lib/formatters'
import { useClientPagination } from '@/composables/useClientPagination'
import MobileActionMenu from '@/components/ui/MobileActionMenu.vue'
import MotionList from '@/components/ui/MotionList.vue'

const props = defineProps({
  carreras: { type: Array, required: true },
  filtered: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: true },
  canDeactivate: { type: Boolean, default: true },
  animate: { type: Boolean, default: true },
})

defineEmits(['edit', 'deactivate'])

const sortedCarreras = computed(() =>
  [...props.carreras].sort((a, b) =>
    (a.nombre || '').localeCompare(b.nombre || '', 'es', { sensitivity: 'base' }),
  ),
)

const {
  page,
  pageSize,
  pageSizes,
  totalPages,
  paginatedItems: paginatedCarreras,
  goToPage,
} = useClientPagination(sortedCarreras)

// El desglose solo cuenta como cargado cuando las dos partes tienen valor. Con
// una sola, el reparto no se puede derivar y el recibo sale sin desglose.
function tieneDesglose(carrera) {
  return (
    carrera.cuota_programatica !== null
    && carrera.cuota_programatica !== undefined
    && carrera.cuota_programatica !== ''
    && carrera.cuota_extraprogramatica !== null
    && carrera.cuota_extraprogramatica !== undefined
    && carrera.cuota_extraprogramatica !== ''
  )
}

function typeLabel(type) {
  const labels = { carrera: 'Carrera', curso: 'Curso' }
  return labels[type] || 'Carrera'
}

function typeIcon(type) {
  return type === 'curso' ? BookOpenIcon : AcademicCapIcon
}
</script>

<style scoped>
.careers-list-card {
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
}

.careers-list-head {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  padding: 1.1rem 1.25rem;
  border-bottom: 1px solid var(--border);
}

.careers-list-title {
  display: flex;
  gap: 0.85rem;
  align-items: center;
}

.careers-list-title h2 {
  margin: 0.1rem 0 0.2rem;
  font-size: 1.05rem;
}

.careers-list-title p:last-child {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.careers-list-icon {
  display: grid;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.8rem;
  background: var(--primary-soft);
  color: var(--primary);
}

.careers-list-icon svg {
  width: 1.3rem;
}

.careers-list-count {
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  background: var(--surface-muted, #f1f5f9);
  color: var(--text-secondary);
  font-size: 0.8rem;
  white-space: nowrap;
}

.careers-table-wrap {
  overflow-x: auto;
}

.careers-table {
  width: 100%;
  border-collapse: collapse;
}

.careers-table th,
.careers-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
  font-size: 0.88rem;
  vertical-align: middle;
}

.careers-table th {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-secondary);
}

.careers-name-cell {
  display: flex;
  gap: 0.6rem;
  align-items: center;
}

.careers-name-cell strong {
  display: block;
}

.careers-name-cell small {
  color: var(--text-secondary);
  font-size: 0.78rem;
}

.careers-type-icon {
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  flex: 0 0 auto;
  border-radius: 0.6rem;
  background: #e0f2fe;
  color: #0369a1;
}

.careers-type-icon.type-curso {
  background: #fef3c7;
  color: #b45309;
}

.careers-type-icon svg {
  width: 1.05rem;
}

.careers-type-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: #e0f2fe;
  color: #0369a1;
  font-size: 0.75rem;
  font-weight: 600;
}

.careers-type-badge.type-curso {
  background: #fef3c7;
  color: #b45309;
}

.careers-amount {
  font-weight: 700;
  white-space: nowrap;
}

.careers-plan,
.careers-muted {
  color: var(--text-secondary);
  white-space: nowrap;
}

.careers-split {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  white-space: nowrap;
}

.careers-split span {
  display: flex;
  gap: 0.4rem;
  align-items: baseline;
  justify-content: space-between;
}

.careers-split small {
  color: var(--text-secondary);
  font-size: 0.72rem;
}

.careers-split strong {
  font-size: 0.85rem;
}

.careers-missing {
  display: inline-flex;
  gap: 0.3rem;
  align-items: center;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: #fff7ed;
  color: #9a3412;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.careers-missing svg {
  width: 0.9rem;
}

.careers-status {
  display: inline-flex;
  gap: 0.3rem;
  align-items: center;
  font-size: 0.8rem;
  white-space: nowrap;
}

.careers-status svg {
  width: 1rem;
}

.careers-status.active {
  color: #15803d;
}

.careers-status.inactive {
  color: var(--text-secondary);
}

.careers-row-actions {
  display: flex;
  gap: 0.35rem;
  justify-content: flex-end;
}

.careers-row-actions button {
  display: grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
}

.careers-row-actions button:hover {
  color: var(--primary);
  border-color: var(--primary);
}

.careers-row-actions button.deactivate:hover {
  color: #b91c1c;
  border-color: #b91c1c;
}

.careers-row-actions svg {
  width: 1.05rem;
}

.careers-mobile-list {
  display: none;
}

.careers-split-mobile {
  margin: 0.6rem 0;
  padding: 0.55rem 0.7rem;
  border: 1px solid var(--border);
  border-radius: 0.6rem;
}

.careers-empty-state {
  display: grid;
  gap: 0.35rem;
  justify-items: center;
  padding: 2.5rem 1.25rem;
  text-align: center;
  color: var(--text-secondary);
}

.careers-empty-state span {
  display: grid;
  place-items: center;
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  background: var(--primary-soft);
  color: var(--primary);
}

.careers-empty-state svg {
  width: 1.4rem;
}

.careers-empty-state p {
  margin: 0;
  font-size: 0.85rem;
}

@media (max-width: 900px) {
  .careers-table {
    display: none;
  }

  .careers-mobile-list {
    display: grid;
  }
}
</style>