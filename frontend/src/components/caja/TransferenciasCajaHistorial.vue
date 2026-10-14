<template>
  <section class="transfer-history" aria-labelledby="transferencias-historial-title">
    <header><p class="eyebrow">Trazabilidad</p><h2 id="transferencias-historial-title">Transferencias recientes</h2></header>
    <p v-if="!transferencias.length" class="empty-state">No hay transferencias recientes dentro de tu alcance.</p>
    <ol v-else class="history-list">
      <li v-for="item in transferencias" :key="item.id" class="history-item border-border bg-surface">
        <div class="history-heading"><strong>{{ item.numero_comprobante }}</strong><strong>$ {{ formatMoney(item.importe, { fractionDigits: 2 }) }}</strong></div>
        <p class="history-route">{{ cajaLabel(item.origen) }} <span aria-label="hacia">→</span> {{ cajaLabel(item.destino) }}</p>
        <p>{{ item.motivo }}</p>
        <small>{{ formatDateTime(item.creado) }} · Ejecutó {{ item.actor.nombre || item.actor.username }} ({{ item.actor.username }})</small>
        <small>Movimiento de salida #{{ item.movimiento_origen_id }} · Movimiento de entrada #{{ item.movimiento_destino_id }}</small>
      </li>
    </ol>
  </section>
</template>

<script setup>
import { formatDateTime, formatMoney } from '@/lib/formatters'
defineProps({ transferencias: { type: Array, required: true } })
function cajaLabel(caja) {
  return caja.sucursal_nombre + ' · ' + caja.usuario_nombre + ' · Caja #' + caja.id
}
</script>

<style scoped>
header { margin-bottom: 1rem; }
.history-list { display: grid; gap: .75rem; list-style: none; padding: 0; margin: 0; }
.history-item { border: 1px solid; border-radius: 1rem; padding: 1.25rem; overflow-wrap: anywhere; }
.history-heading { display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
.history-route { font-weight: 600; margin: .75rem 0; }
.history-item small { display: block; color: var(--color-text-secondary); margin-top: .5rem; }
.empty-state { padding: 1.25rem; border: 1px dashed var(--color-border); border-radius: 1rem; }
</style>
