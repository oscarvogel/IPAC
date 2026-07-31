<template>
  <aside class="students-detail-panel border-border bg-surface">
    <template v-if="alumno">
      <header class="students-detail-hero">
        <div class="students-detail-profile">
          <span class="students-avatar students-avatar-large">{{ avatarInitials(alumno) }}</span>
          <div class="students-detail-identity">
            <p class="eyebrow">Ficha del alumno</p>
            <h2>{{ alumno.nombre }} {{ alumno.apellido }}</h2>
            <p>{{ alumno.legajo || 'Sin legajo' }} <span aria-hidden="true">•</span> DNI {{ alumno.dni || '—' }}</p>
          </div>
        </div>

        <button
          type="button"
          class="students-icon-action"
          title="Editar alumno"
          aria-label="Editar alumno"
          @click="$emit('edit')"
        >
          <PencilSquareIcon aria-hidden="true" />
        </button>
      </header>

      <div class="students-detail-status-row">
        <span :class="['students-status', alumno.estado]">
          <component :is="statusIcon" aria-hidden="true" />
          {{ alumno.estado || 'sin estado' }}
        </span>
        <span>{{ alumno.carrera_nombre || 'Sin carrera asignada' }}</span>
      </div>

      <div class="students-detail-actions">
        <button type="button" class="primary" @click="$emit('register-pago')">
          <BanknotesIcon aria-hidden="true" />
          <span>Registrar pago</span>
        </button>
        <button type="button" @click="$emit('generar-cuota')">
          <DocumentPlusIcon aria-hidden="true" />
          <span>Generar cuota</span>
        </button>
      </div>

      <section class="students-info-section" aria-labelledby="student-contact-title">
        <div class="students-section-heading">
          <div>
            <p class="eyebrow">Información</p>
            <h3 id="student-contact-title">Datos personales</h3>
          </div>
        </div>

        <dl class="students-detail-data">
          <div>
            <dt><BuildingStorefrontIcon aria-hidden="true" /> Sucursal</dt>
            <dd>{{ alumno.sucursal_nombre || 'Sin asignar' }}</dd>
          </div>
          <div>
            <dt><AcademicCapIcon aria-hidden="true" /> Carrera</dt>
            <dd>{{ alumno.carrera_nombre || 'Sin asignar' }}</dd>
          </div>
          <div>
            <dt><EnvelopeIcon aria-hidden="true" /> Email</dt>
            <dd>{{ alumno.email || 'Sin email' }}</dd>
          </div>
          <div>
            <dt><PhoneIcon aria-hidden="true" /> Teléfono</dt>
            <dd>{{ alumno.telefono || 'Sin teléfono' }}</dd>
          </div>
        </dl>
      </section>

      <section class="students-concepts" aria-labelledby="student-concepts-title">
        <div class="students-section-heading">
          <div>
            <p class="eyebrow">Facturación</p>
            <h3 id="student-concepts-title">Conceptos asociados</h3>
          </div>
          <span>{{ detailConcepts.length }}</span>
        </div>

        <div v-for="concepto in detailConcepts" :key="concepto.id" class="students-concept-row">
          <span>
            <BookOpenIcon aria-hidden="true" />
            {{ concepto.nombre }}
          </span>
          <strong>$ {{ formatMoney(concepto.importe) }}</strong>
        </div>
        <p v-if="!detailConcepts.length" class="students-inline-empty">
          Sin conceptos activos para esta sucursal.
        </p>
      </section>

      <section class="students-account-summary" aria-label="Resumen de cuenta">
        <div>
          <span>Pagado</span>
          <strong>$ {{ formatMoney(paidTotal) }}</strong>
        </div>
        <div>
          <span>Saldo estimado</span>
          <strong>$ {{ formatMoney(pendingTotal) }}</strong>
        </div>
        <button type="button" @click="$emit('view-estado')">
          <span>Ver estado de cuenta</span>
          <ArrowRightIcon aria-hidden="true" />
        </button>
      </section>

      <button
        type="button"
        :class="['students-state-action', alumno.estado === 'inactivo' ? 'activate' : 'deactivate']"
        @click="$emit('toggle-estado', alumno)"
      >
        <component :is="alumno.estado === 'inactivo' ? ArrowPathIcon : NoSymbolIcon" aria-hidden="true" />
        {{ alumno.estado === 'inactivo' ? 'Reactivar alumno' : 'Dar de baja' }}
      </button>
    </template>

    <div v-else class="students-detail-empty">
      <span><IdentificationIcon aria-hidden="true" /></span>
      <strong>Seleccioná un alumno</strong>
      <p>Su información académica y estado de cuenta aparecerán acá.</p>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import {
  AcademicCapIcon,
  ArrowPathIcon,
  ArrowRightIcon,
  BanknotesIcon,
  BookOpenIcon,
  BuildingStorefrontIcon,
  CheckCircleIcon,
  DocumentPlusIcon,
  EnvelopeIcon,
  IdentificationIcon,
  NoSymbolIcon,
  PauseCircleIcon,
  PencilSquareIcon,
  PhoneIcon,
} from '@heroicons/vue/24/outline'
import { formatMoney } from '@/lib/formatters'

const props = defineProps({
  alumno: { type: Object, default: null },
  conceptos: { type: Array, default: () => [] },
  pagos: { type: Array, default: () => [] },
})

defineEmits(['register-pago', 'edit', 'view-estado', 'generar-cuota', 'toggle-estado'])

const statusIcon = computed(() =>
  props.alumno?.estado === 'activo' ? CheckCircleIcon : PauseCircleIcon,
)

const detailConcepts = computed(() => {
  if (!props.alumno) return []
  return props.conceptos
    .filter((concepto) => concepto.activo)
    .filter((concepto) => concepto.sucursal === props.alumno.sucursal)
    .slice(0, 3)
})

const paidTotal = computed(() => {
  if (!props.alumno) return 0
  return props.pagos
    .filter((pago) => pago.alumno === props.alumno.id)
    .reduce((sum, pago) => sum + Number(pago.importe || 0), 0)
})

const pendingTotal = computed(() => {
  const conceptsTotal = detailConcepts.value.reduce(
    (sum, concepto) => sum + Number(concepto.importe || 0),
    0,
  )
  return Math.max(conceptsTotal - paidTotal.value, 0)
})

function avatarInitials(alumno) {
  const name = (alumno.nombre || '').trim()
  const surname = (alumno.apellido || '').trim()
  return `${name.slice(0, 1)}${surname.slice(0, 1)}`.toUpperCase() || '?'
}
</script>
