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
          v-if="canEdit"
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
        <span>{{ activeMatricula?.carrera_nombre || 'Sin matrícula activa' }}</span>
      </div>

      <div class="students-detail-actions">
        <button v-if="canRegisterPago" type="button" class="primary" @click="$emit('register-pago')">
          <BanknotesIcon aria-hidden="true" />
          <span>Registrar pago</span>
        </button>
        <button v-if="canGenerateFee" type="button" @click="$emit('generar-cuota')">
          <DocumentPlusIcon aria-hidden="true" />
          <span>Generar cuota</span>
        </button>
        <button type="button" @click="$emit('view-estado')">
          <ArrowRightIcon aria-hidden="true" />
          <span>Estado de cuenta</span>
        </button>
      </div>

      <nav class="student-detail-tabs" aria-label="Secciones de la ficha del alumno">
        <button
          v-for="tab in detailTabs"
          :key="tab.id"
          type="button"
          :class="{ active: activeTab === tab.id }"
          :aria-pressed="activeTab === tab.id"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </nav>

      <section v-show="activeTab === 'datos'" class="students-info-section" aria-labelledby="student-contact-title">
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
            <dt><AcademicCapIcon aria-hidden="true" /> Trayectoria académica</dt>
            <dd>{{ activeMatricula?.carrera_nombre || 'Sin matrícula activa' }}</dd>
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

      <MatriculasPanel
        v-show="activeTab === 'matriculas'"
        :alumno="alumno"
        :can-manage="canManageMatriculas"
        @active-changed="handleActiveMatricula"
        @changed="$emit('matricula-changed')"
      />

      <section v-show="activeTab === 'cuenta'" class="students-concepts" aria-labelledby="student-concepts-title">
        <div class="students-section-heading">
          <div>
            <p class="eyebrow">Facturación</p>
            <h3 id="student-concepts-title">Conceptos facturables</h3>
            <p class="students-concepts-help">Son conceptos activos de la sucursal; no representan una matrícula vigente.</p>
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

      <section v-show="activeTab === 'cuenta'" class="students-account-summary" aria-label="Resumen de cuenta">
        <div>
          <span>Deuda pendiente</span>
          <strong>$ {{ formatMoney(alumno.deuda_total || 0) }}</strong>
        </div>
        <div>
          <span>Saldo a favor</span>
          <strong>$ {{ formatMoney(alumno.saldo_a_favor || 0) }}</strong>
        </div>
        <button type="button" @click="$emit('view-estado')">
          <span>Ver estado de cuenta</span>
          <ArrowRightIcon aria-hidden="true" />
        </button>
      </section>

      <section v-show="activeTab === 'historial'" class="students-info-section student-history" aria-labelledby="student-history-title">
        <div class="students-section-heading">
          <div>
            <p class="eyebrow">Actividad</p>
            <h3 id="student-history-title">Historial reciente</h3>
          </div>
        </div>
        <ol v-if="studentPayments.length" class="student-history-list">
          <li v-for="pago in studentPayments" :key="pago.id">
            <span><BanknotesIcon aria-hidden="true" /></span>
            <span><strong>{{ pago.numero_recibo || 'Pago registrado' }}</strong><small>{{ pago.fecha }} · {{ pago.medio_label || pago.medio }}</small></span>
            <strong>$ {{ formatMoney(pago.importe) }}</strong>
          </li>
        </ol>
        <p v-else class="students-inline-empty">Todavía no hay pagos registrados para este alumno.</p>
      </section>

      <button
        v-if="canToggleState"
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
import { computed, ref, watch } from 'vue'
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
import MatriculasPanel from '@/components/alumnos/MatriculasPanel.vue'

const props = defineProps({
  alumno: { type: Object, default: null },
  conceptos: { type: Array, default: () => [] },
  pagos: { type: Array, default: () => [] },
  canEdit: { type: Boolean, default: true },
  canRegisterPago: { type: Boolean, default: true },
  canGenerateFee: { type: Boolean, default: true },
  canToggleState: { type: Boolean, default: true },
  canManageMatriculas: { type: Boolean, default: false },
})

const activeMatricula = ref(null)
const activeTab = ref('datos')
const detailTabs = [
  { id: 'datos', label: 'Datos' },
  { id: 'cuenta', label: 'Cuenta' },
  { id: 'matriculas', label: 'Matrículas' },
  { id: 'historial', label: 'Historial' },
]

watch(() => props.alumno?.id, () => {
  activeMatricula.value = null
  activeTab.value = 'datos'
}, { immediate: true })

defineEmits(['register-pago', 'edit', 'view-estado', 'generar-cuota', 'toggle-estado', 'matricula-changed'])

function handleActiveMatricula(matricula) {
  activeMatricula.value = matricula
}

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

const studentPayments = computed(() => {
  if (!props.alumno) return []
  return props.pagos
    .filter((pago) => pago.alumno === props.alumno.id)
    .slice()
    .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
    .slice(0, 8)
})

function avatarInitials(alumno) {
  const name = (alumno.nombre || '').trim()
  const surname = (alumno.apellido || '').trim()
  return `${name.slice(0, 1)}${surname.slice(0, 1)}`.toUpperCase() || '?'
}
</script>

<style scoped>
.student-detail-tabs { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .25rem; padding: .25rem; border: 1px solid var(--border); border-radius: .7rem; background: var(--background); }
.student-detail-tabs button { min-height: 2.25rem; border: 0; border-radius: .5rem; padding: .35rem .45rem; background: transparent; color: var(--text-secondary); font-size: .72rem; font-weight: 800; }
.student-detail-tabs button.active { background: var(--primary); color: #fff; }
.student-history-list { margin: 0; padding: 0; display: grid; list-style: none; }
.student-history-list li { padding: .65rem 0; display: grid; grid-template-columns: 2rem minmax(0, 1fr) auto; align-items: center; gap: .55rem; border-bottom: 1px solid var(--border); }
.student-history-list li > span:first-child { width: 2rem; height: 2rem; display: grid; place-items: center; border-radius: .55rem; background: var(--primary-soft); color: var(--primary); }
.student-history-list svg { width: 1.05rem; }
.student-history-list span:nth-child(2) { min-width: 0; display: grid; gap: .15rem; }
.student-history-list small { overflow: hidden; color: var(--text-secondary); text-overflow: ellipsis; white-space: nowrap; }
.students-concepts-help { margin-top: .25rem; color: var(--text-secondary); font-size: .72rem; line-height: 1.35; }
@media (max-width: 430px) { .student-detail-tabs { grid-template-columns: repeat(2, 1fr); } }
</style>
