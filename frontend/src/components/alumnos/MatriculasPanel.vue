<template>
  <section class="matriculas-panel students-info-section" aria-labelledby="matriculas-title">
    <div class="students-section-heading">
      <div>
        <p class="eyebrow">Trayectoria académica</p>
        <h3 id="matriculas-title">Matrículas</h3>
      </div>
      <button v-if="canManage" type="button" class="matriculas-add-button" @click="openCreate">
        Nueva
      </button>
    </div>

    <p v-if="loading" class="students-inline-empty">Cargando matrículas...</p>
    <p v-else-if="error" class="students-inline-error" role="alert">{{ error }}</p>
    <template v-else>
      <article v-if="activeMatricula" class="matricula-active-card">
        <div>
          <span class="matricula-status active">Activa</span>
          <strong>{{ activeMatricula.carrera_nombre }}</strong>
          <small>{{ formatDate(activeMatricula.fecha_inicio) }} · {{ activeMatricula.sucursal_nombre || 'Sucursal asignada' }}</small>
          <p v-if="activeMatricula.observacion">{{ activeMatricula.observacion }}</p>
        </div>
        <div v-if="canManage" class="matricula-actions">
          <button type="button" @click="openEdit(activeMatricula)">Editar</button>
          <button type="button" @click="requestFinalize(activeMatricula)">Finalizar</button>
        </div>
      </article>

      <div v-if="history.length" class="matriculas-history">
        <span class="matriculas-history-title">Historial</span>
        <article v-for="matricula in history" :key="matricula.id" class="matricula-history-row">
          <div>
            <strong>{{ matricula.carrera_nombre }}</strong>
            <small>
              {{ formatDate(matricula.fecha_inicio) }}
              <template v-if="matricula.fecha_fin"> → {{ formatDate(matricula.fecha_fin) }}</template>
              · {{ matricula.observacion || 'Sin observación' }}
            </small>
          </div>
          <span :class="['matricula-status', matricula.estado]">{{ stateLabel(matricula.estado) }}</span>
          <button v-if="canManage && matricula.estado !== 'anulada'" type="button" @click="openEdit(matricula)">Editar</button>
        </article>
      </div>

      <p v-if="!activeMatricula && !history.length" class="students-inline-empty">
        Este alumno todavía no tiene matrículas registradas.
      </p>
    </template>

    <MatriculaForm
      :open="showForm"
      :alumno="alumno"
      :matricula="editingMatricula"
      @close="closeForm"
      @saved="onSaved"
    />
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import MatriculaForm from '@/components/alumnos/MatriculaForm.vue'
import { useMatriculas } from '@/composables/useMatriculas'
import { useToast } from '@/composables/useToast'
import { confirmFinalizarMatricula } from '@/lib/swal'
import { formatDate } from '@/lib/formatters'

const props = defineProps({
  alumno: { type: Object, default: null },
  canManage: { type: Boolean, default: false },
})

const emit = defineEmits(['changed'])
const { matriculas, loading, error, loadMatriculas, finalizarMatricula } = useMatriculas()
const toast = useToast()
const showForm = ref(false)
const editingMatricula = ref(null)

const activeMatricula = computed(() => matriculas.value.find((matricula) => matricula.estado === 'activa') || null)
const history = computed(() => matriculas.value.filter((matricula) => matricula.estado !== 'activa'))

watch(() => props.alumno?.id, async (alumnoId) => {
  try {
    await loadMatriculas(alumnoId)
  } catch {
    // El estado inline del panel ya expone el error normalizado del composable.
  }
}, { immediate: true })

function openCreate() {
  editingMatricula.value = null
  showForm.value = true
}

function openEdit(matricula) {
  editingMatricula.value = matricula
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingMatricula.value = null
}

async function onSaved() {
  closeForm()
  await loadMatriculas(props.alumno?.id)
  emit('changed')
}

async function requestFinalize(matricula) {
  const confirmation = await confirmFinalizarMatricula({
    alumno: `${props.alumno?.nombre || ''} ${props.alumno?.apellido || ''}`.trim(),
    carrera: matricula.carrera_nombre,
    fechaInicio: formatDate(matricula.fecha_inicio),
  })
  if (!confirmation.isConfirmed) return

  try {
    await finalizarMatricula(matricula.id)
    toast.success('Matrícula finalizada')
    await loadMatriculas(props.alumno?.id)
    emit('changed')
  } catch (err) {
    toast.error(err.message || 'No se pudo finalizar la matrícula.')
  }
}

function stateLabel(state) {
  return { activa: 'Activa', finalizada: 'Finalizada', anulada: 'Anulada' }[state] || state
}
</script>

<style scoped>
.matriculas-panel {
  margin-top: 18px;
}

.matriculas-add-button,
.matricula-actions button,
.matricula-history-row > button {
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--primary);
  background: var(--surface);
  font-size: 11px;
  font-weight: 700;
}

.matriculas-add-button {
  padding: 7px 10px;
}

.matricula-active-card {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border: 1px solid color-mix(in srgb, var(--success) 32%, var(--border));
  border-radius: 10px;
  background: color-mix(in srgb, var(--success) 6%, var(--surface));
}

.matricula-active-card strong,
.matricula-active-card small,
.matricula-active-card p,
.matricula-history-row strong,
.matricula-history-row small {
  display: block;
}

.matricula-active-card small,
.matricula-active-card p,
.matricula-history-row small {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 11px;
}

.matricula-active-card p {
  margin-bottom: 0;
}

.matricula-status {
  display: inline-flex;
  margin-bottom: 5px;
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 760;
  text-transform: uppercase;
}

.matricula-status.active,
.matricula-status.activa {
  color: var(--success);
}

.matricula-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.matricula-actions button,
.matricula-history-row > button {
  padding: 5px 8px;
}

.matriculas-history {
  margin-top: 14px;
}

.matriculas-history-title {
  display: block;
  margin-bottom: 7px;
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 760;
  letter-spacing: .08em;
  text-transform: uppercase;
}

.matricula-history-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: 10px;
  padding: 9px 0;
  border-top: 1px solid var(--border);
}

.matricula-history-row .matricula-status {
  margin: 0;
}

@media (max-width: 520px) {
  .matricula-active-card {
    flex-direction: column;
  }

  .matricula-actions {
    flex-direction: row;
    align-items: center;
  }

  .matricula-history-row {
    grid-template-columns: 1fr auto;
  }

  .matricula-history-row > button {
    grid-column: 2;
  }
}
</style>
