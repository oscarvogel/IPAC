<template>
  <section class="print-recibo" aria-hidden="true">
    <header>
      <strong>IPAC</strong>
      <span>Recibo de pago</span>
    </header>
    <div class="recibo-header">
      <h1>Recibo N&deg; {{ recibo?.numero }}</h1>
      <p>{{ recibo?.pago?.sucursal_nombre }} &middot; {{ formatDate(recibo?.pago?.fecha) }}</p>
      <strong v-if="recibo?.pago?.estado === 'anulado'" class="recibo-cancelled">ANULADO</strong>
    </div>
    <table class="recibo-alumno">
      <tbody>
        <tr><td>Alumno</td><td><strong>{{ recibo?.pago?.alumno_nombre || '—' }}</strong></td></tr>
        <tr><td>Legajo</td><td><strong>{{ recibo?.pago?.alumno_legajo || '—' }}</strong></td></tr>
        <tr><td>Medio</td><td><strong>{{ recibo?.pago?.medio || '—' }}</strong></td></tr>
      </tbody>
    </table>
    <table class="recibo-detalle">
      <thead>
        <tr><th>Concepto</th><th>Periodo</th><th>Importe</th></tr>
      </thead>
      <tbody>
        <tr v-for="(app, i) in recibo?.aplicaciones || []" :key="i" :class="{ 'recibo-application-cancelled': app.activa === false }">
          <td>{{ app.concepto }}</td>
          <td>{{ app.periodo }}</td>
          <td>$ {{ formatMoney(app.importe) }}</td>
        </tr>
        <tr v-if="!(recibo?.aplicaciones?.length)">
          <td colspan="3">{{ recibo?.pago?.concepto_nombre || 'Pago a cuenta' }}</td>
        </tr>
      </tbody>
      <tfoot>
        <tr><td colspan="2"><strong>Total</strong></td><td><strong>$ {{ formatMoney(recibo?.pago?.importe) }}</strong></td></tr>
        <tr v-if="recibo?.pago?.saldo_pendiente_posterior != null">
          <td colspan="2"><strong>Saldo pendiente posterior</strong></td>
          <td><strong>$ {{ formatMoney(recibo.pago.saldo_pendiente_posterior) }}</strong></td>
        </tr>
      </tfoot>
    </table>
    <p class="recibo-obs" v-if="recibo?.pago?.observacion">
      Obs: {{ recibo.pago.observacion }}
    </p>
    <p v-if="recibo?.pago?.estado === 'anulado'" class="recibo-void-reason">
      Motivo de anulación: {{ recibo.pago.motivo_anulacion }}
    </p>
    <footer class="recibo-footer">
      <span>Emitido: {{ formatDateTime(recibo?.emitido_en) }}</span>
      <span>Usuario: {{ recibo?.pago?.usuario_nombre || '—' }}</span>
    </footer>
  </section>
</template>

<script setup>
import { formatDate, formatDateTime, formatMoney } from '@/lib/formatters'

defineProps({
  recibo: { type: Object, default: null },
})
</script>

<style scoped>
.print-recibo {
  display: none;
}

@media print {
  .print-recibo {
    display: block;
    position: absolute;
    inset: 0;
    padding: 32px;
    color: #111827;
    background: white;
    font-family: ui-sans-serif, system-ui, sans-serif;
  }

  .print-recibo header {
    display: flex;
    justify-content: space-between;
    padding-bottom: 14px;
    border-bottom: 2px solid #111827;
    font-size: 14px;
  }

  .print-recibo h1 {
    margin: 20px 0 4px;
    font-size: 24px;
  }

  .recibo-header p {
    color: #6b7280;
    margin-bottom: 16px;
  }

  .recibo-cancelled {
    display: inline-block;
    margin-bottom: 16px;
    padding: 6px 12px;
    border: 2px solid #b91c1c;
    color: #b91c1c;
    font-size: 20px;
    letter-spacing: .12em;
  }

  .recibo-application-cancelled {
    text-decoration: line-through;
  }

  .recibo-void-reason {
    margin-bottom: 20px;
    color: #b91c1c;
    font-weight: 700;
  }

  .recibo-alumno {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
  }

  .recibo-alumno td {
    padding: 6px 12px;
    border: 1px solid #d1d5db;
    font-size: 14px;
  }

  .recibo-alumno td:first-child {
    width: 100px;
    color: #6b7280;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.05em;
  }

  .recibo-detalle {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 12px;
  }

  .recibo-detalle th,
  .recibo-detalle td {
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    text-align: left;
    font-size: 13px;
  }

  .recibo-detalle th {
    background: #f3f4f6;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .recibo-detalle tfoot td {
    font-size: 15px;
  }

  .recibo-obs {
    color: #6b7280;
    font-size: 12px;
    margin-bottom: 20px;
  }

  .recibo-footer {
    display: flex;
    justify-content: space-between;
    padding-top: 14px;
    border-top: 1px solid #d1d5db;
    color: #6b7280;
    font-size: 12px;
  }
}
</style>
