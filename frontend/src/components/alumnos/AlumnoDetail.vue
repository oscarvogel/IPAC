<template>
  <aside class="detail-panel panel">
    <template v-if="alumno">
      <div class="detail-hero">
        <span class="avatar large">{{ avatarInitials(alumno) }}</span>
        <div>
          <p class="eyebrow">Cuenta del alumno</p>
          <h2>{{ alumno.nombre }} {{ alumno.apellido }}</h2>
          <small>{{ alumno.legajo }} · DNI {{ alumno.dni }}</small>
        </div>
      </div>

      <div class="detail-actions">
        <button type="button" @click="$emit('register-pago')">Registrar pago</button>
        <button type="button" @click="$emit('edit')">Editar alumno</button>
      </div>

      <dl class="detail-data">
        <div><dt>Sucursal</dt><dd>{{ alumno.sucursal_nombre }}</dd></div>
        <div><dt>Carrera</dt><dd>{{ alumno.carrera_nombre || 'Sin asignar' }}</dd></div>
        <div><dt>Email</dt><dd>{{ alumno.email || 'Sin email' }}</dd></div>
        <div><dt>Telefono</dt><dd>{{ alumno.telefono || 'Sin telefono' }}</dd></div>
      </dl>

      <div class="mini-ledger">
        <div class="panel-head compact">
          <h3>Conceptos asociados</h3>
          <span>{{ detailConcepts.length }}</span>
        </div>
        <div v-for="concepto in detailConcepts" :key="concepto.id" class="ledger-row">
          <span>{{ concepto.nombre }}</span>
          <strong>$ {{ formatMoney(concepto.importe) }}</strong>
        </div>
        <p v-if="!detailConcepts.length" class="empty-state flat">
          Sin conceptos activos para esta sucursal.
        </p>
      </div>

      <div class="account-summary">
        <div><span>Pagado</span><strong>$ {{ formatMoney(paidTotal) }}</strong></div>
        <div><span>Saldo</span><strong>$ {{ formatMoney(pendingTotal) }}</strong></div>
        <button type="button" @click="$emit('view-estado')">Ver estado de cuenta</button>
      </div>
    </template>
    <p v-else class="empty-state flat">Selecciona un alumno de la lista para ver su ficha.</p>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney } from '@/lib/formatters'

const props = defineProps({
  alumno: { type: Object, default: null },
  conceptos: { type: Array, default: () => [] },
  pagos: { type: Array, default: () => [] },
})

defineEmits(['register-pago', 'edit', 'view-estado'])

const detailConcepts = computed(() => {
  if (!props.alumno) return []
  return props.conceptos
    .filter((c) => c.activo)
    .filter((c) => c.sucursal === props.alumno.sucursal)
    .slice(0, 3)
})

const paidTotal = computed(() => {
  if (!props.alumno) return 0
  return props.pagos
    .filter((p) => p.alumno === props.alumno.id)
    .reduce((sum, p) => sum + Number(p.importe || 0), 0)
})

const pendingTotal = computed(() => {
  const conceptsTotal = detailConcepts.value.reduce(
    (sum, c) => sum + Number(c.importe || 0),
    0,
  )
  return Math.max(conceptsTotal - paidTotal.value, 0)
})

function avatarInitials(alumno) {
  const n = (alumno.nombre || '').trim()
  const a = (alumno.apellido || '').trim()
  return `${n.slice(0, 1)}${a.slice(0, 1)}`.toUpperCase() || '?'
}
</script>
