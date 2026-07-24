<template>
  <div class="cash-hero panel">
    <div>
      <p class="eyebrow">Caja del dia</p>
      <h2>{{ sucursalLabel }}</h2>
      <span v-if="cajaHoy">{{ cajaHoy.fecha }} · {{ cajaHoy.estado }}</span>
    </div>
    <div class="cash-actions">
      <button type="button" @click="$emit('print')">Imprimir resumen</button>
      <button type="button" :disabled="!puedeMover" @click="$emit('movimiento', 'ingreso')">Ingreso</button>
      <button type="button" :disabled="!puedeMover" @click="$emit('movimiento', 'egreso')">Egreso</button>
      <button type="button" :disabled="!puedeMover" @click="$emit('movimiento', 'retiro')">Retiro</button>
      <button class="close-cash" type="button" :disabled="!puedeMover" @click="$emit('cerrar')">Cerrar caja</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  cajaHoy: { type: Object, default: null },
  fallbackSucursal: { type: String, default: '' },
  puedeMover: { type: Boolean, default: false },
})

defineEmits(['print', 'movimiento', 'cerrar'])

const sucursalLabel = computed(
  () => props.cajaHoy?.sucursal_nombre || props.fallbackSucursal || '',
)
</script>
