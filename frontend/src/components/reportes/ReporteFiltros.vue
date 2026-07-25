<template>
  <div class="report-filters topbar-filters">
    <label>
      <span>Desde</span>
      <input v-model="local.desde" type="date" />
    </label>
    <label>
      <span>Hasta</span>
      <input v-model="local.hasta" type="date" />
    </label>
    <label>
      <span>Sucursal</span>
      <select v-model="local.sucursal" class="compact-select">
        <option value="">Todas</option>
        <option v-for="sucursal in sucursales" :key="sucursal.id" :value="sucursal.id">
          {{ sucursal.nombre }}
        </option>
      </select>
    </label>
    <label>
      <span>Medio</span>
      <select v-model="local.medio" class="compact-select">
        <option value="">Todos</option>
        <option value="efectivo">Efectivo</option>
        <option value="transferencia">Transferencia</option>
        <option value="tarjeta">Tarjeta</option>
        <option value="otro">Otro</option>
      </select>
    </label>
    <button class="primary-button" type="button" :disabled="loading" @click="aplicar">
      {{ loading ? 'Cargando...' : 'Aplicar filtros' }}
    </button>
    <button class="secondary-button" type="button" :disabled="loading" @click="$emit('exportar')">
      Exportar CSV
    </button>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  filtros: { type: Object, required: true },
  sucursales: { type: Array, required: true },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['update:filtros', 'aplicar', 'exportar'])

const local = reactive({ ...props.filtros })

watch(
  () => props.filtros,
  (nuevo) => {
    Object.assign(local, nuevo)
  },
  { deep: true },
)

function aplicar() {
  emit('update:filtros', { ...local })
  emit('aplicar')
}
</script>

<style scoped>
.report-filters {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.report-filters label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.85rem;
  color: #4a4a55;
}

.report-filters input,
.report-filters select {
  min-width: 140px;
}
</style>
