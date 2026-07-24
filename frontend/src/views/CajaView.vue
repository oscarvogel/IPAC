<template>
  <section class="cash-screen">
    <div class="cash-hero panel">
      <div>
        <p class="eyebrow">Caja del dia</p>
        <h2>{{ cajaHoy?.sucursal_nombre || auth.user?.perfil?.sucursal?.nombre }}</h2>
        <span>{{ cajaHoy?.fecha }} · {{ cajaHoy?.estado }}</span>
      </div>
      <div class="cash-actions">
        <button type="button" @click="printCajaResumen">Imprimir resumen</button>
        <button type="button" :disabled="!puedeMover" @click="openMovimiento('ingreso')">Ingreso</button>
        <button type="button" :disabled="!puedeMover" @click="openMovimiento('egreso')">Egreso</button>
        <button type="button" :disabled="!puedeMover" @click="openMovimiento('retiro')">Retiro</button>
        <button class="close-cash" type="button" :disabled="!puedeMover" @click="openCerrar">Cerrar caja</button>
      </div>
    </div>

    <div class="stats-grid cash-stats">
      <article class="stat-card">
        <span>Total esperado</span>
        <strong>$ {{ formatMoney(cajaTotales.total) }}</strong>
        <small>incluye pagos y movimientos</small>
      </article>
      <article class="stat-card">
        <span>Efectivo</span>
        <strong>$ {{ formatMoney(cajaTotales.efectivo) }}</strong>
        <small>saldo de efectivo</small>
      </article>
      <article class="stat-card">
        <span>Transferencia</span>
        <strong>$ {{ formatMoney(cajaTotales.transferencia) }}</strong>
        <small>pagos bancarios</small>
      </article>
      <article class="stat-card">
        <span>Movimientos</span>
        <strong>{{ cajaMovimientos.length }}</strong>
        <small>registrados hoy</small>
      </article>
    </div>

    <div class="panel table-card">
      <div class="panel-head">
        <div>
          <h2>Movimientos de caja</h2>
          <p>Pagos, ingresos, egresos, retiros y pases</p>
        </div>
      </div>
      <table>
        <thead>
          <tr><th>Tipo</th><th>Medio</th><th>Descripcion</th><th>Importe</th></tr>
        </thead>
        <tbody>
          <tr v-for="movimiento in cajaMovimientos" :key="movimiento.id">
            <td><span class="table-badge">{{ movimiento.tipo_label }}</span></td>
            <td>{{ movimiento.medio }}</td>
            <td>{{ movimiento.descripcion || 'Sin descripcion' }}</td>
            <td>$ {{ formatMoney(movimiento.importe) }}</td>
          </tr>
        </tbody>
      </table>
      <p v-if="!cajaMovimientos.length" class="empty-state flat">
        Todavia no hay movimientos en esta caja.
      </p>
    </div>

    <section class="cash-print-summary" aria-hidden="true">
      <header><strong>IPAC</strong><span>Resumen de caja</span></header>
      <h1>{{ cajaHoy?.sucursal_nombre || auth.user?.perfil?.sucursal?.nombre }}</h1>
      <p>{{ cajaHoy?.fecha }} · Usuario: {{ auth.user?.username }} · Estado: {{ cajaHoy?.estado }}</p>
      <div class="print-totals">
        <div><span>Total esperado</span><strong>$ {{ formatMoney(cajaTotales.total) }}</strong></div>
        <div><span>Efectivo</span><strong>$ {{ formatMoney(cajaTotales.efectivo) }}</strong></div>
        <div><span>Transferencia</span><strong>$ {{ formatMoney(cajaTotales.transferencia) }}</strong></div>
        <div v-if="cajaHoy?.estado === 'cerrada'">
          <span>Total contado</span><strong>$ {{ formatMoney(cajaHoy.total_contado) }}</strong>
        </div>
        <div v-if="cajaHoy?.estado === 'cerrada'">
          <span>Diferencia</span><strong>$ {{ formatMoney(cajaHoy.diferencia) }}</strong>
        </div>
      </div>
      <table>
        <thead>
          <tr><th>Tipo</th><th>Medio</th><th>Descripcion</th><th>Importe</th></tr>
        </thead>
        <tbody>
          <tr v-for="movimiento in cajaMovimientos" :key="`print-${movimiento.id}`">
            <td>{{ movimiento.tipo_label }}</td>
            <td>{{ movimiento.medio }}</td>
            <td>{{ movimiento.descripcion || 'Sin descripcion' }}</td>
            <td>$ {{ formatMoney(movimiento.importe) }}</td>
          </tr>
          <tr v-if="!cajaMovimientos.length"><td colspan="4">No hay movimientos registrados.</td></tr>
        </tbody>
      </table>
    </section>

    <Teleport to="body">
      <div v-if="showMovimiento" class="modal-backdrop" @click.self="closeMovimiento">
        <form class="modal-card compact-modal" @submit.prevent="submitMovimiento">
          <header class="modal-head">
            <div>
              <p class="eyebrow">Movimiento de caja</p>
              <h2>Registrar {{ movimientoForm.tipo }}</h2>
              <span>Caja {{ cajaHoy?.sucursal_nombre }} · {{ cajaHoy?.fecha }}</span>
            </div>
            <button class="icon-button" type="button" aria-label="Cerrar" @click="closeMovimiento">×</button>
          </header>
          <section class="modal-section">
            <div class="modal-grid">
              <label>
                Tipo
                <select v-model="movimientoForm.tipo">
                  <option value="ingreso">Ingreso</option>
                  <option value="egreso">Egreso</option>
                  <option value="retiro">Retiro</option>
                  <option value="pase">Pase</option>
                </select>
              </label>
              <label>
                Medio
                <select v-model="movimientoForm.medio">
                  <option value="efectivo">Efectivo</option>
                  <option value="transferencia">Transferencia</option>
                  <option value="tarjeta">Tarjeta</option>
                  <option value="otro">Otro</option>
                </select>
              </label>
              <label>Importe<input v-model.number="movimientoForm.importe" type="number" min="0" step="0.01" required /></label>
              <label>Descripcion<input v-model="movimientoForm.descripcion" required /></label>
            </div>
          </section>
          <footer class="modal-actions">
            <button class="secondary-button" type="button" @click="closeMovimiento">Cancelar</button>
            <button class="primary-button modal-submit" :disabled="loading" type="submit">Guardar movimiento</button>
          </footer>
        </form>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="showCerrar" class="modal-backdrop" @click.self="showCerrar = false">
        <form class="modal-card compact-modal" @submit.prevent="submitCerrar">
          <header class="modal-head">
            <div>
              <p class="eyebrow">Cierre de caja</p>
              <h2>Cerrar caja del dia</h2>
              <span>Total esperado: $ {{ formatMoney(cajaTotales.total) }}</span>
            </div>
            <button class="icon-button" type="button" aria-label="Cerrar" @click="showCerrar = false">×</button>
          </header>
          <section class="modal-section">
            <div class="modal-grid">
              <label>Total contado<input v-model.number="cierreForm.total_contado" type="number" step="0.01" required /></label>
            </div>
          </section>
          <footer class="modal-actions">
            <button class="secondary-button" type="button" @click="showCerrar = false">Cancelar</button>
            <button class="primary-button modal-submit" :disabled="loading" type="submit">Confirmar cierre</button>
          </footer>
        </form>
      </div>
    </Teleport>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { useCaja } from '@/composables/useCaja'
import { useToast } from '@/composables/useToast'
import { formatMoney } from '@/lib/formatters'

const auth = useAuth()
const caja = useCaja()
const toast = useToast()

const { cajaHoy, cajaMovimientos, cajaTotales, loading } = caja

const showMovimiento = ref(false)
const showCerrar = ref(false)

const movimientoForm = reactive({
  tipo: 'egreso',
  medio: 'efectivo',
  importe: '',
  descripcion: '',
})

const cierreForm = reactive({
  total_contado: '',
})

const puedeMover = computed(() => cajaHoy.value && cajaHoy.value.estado !== 'cerrada')

function openMovimiento(tipo = 'egreso') {
  Object.assign(movimientoForm, { tipo, medio: 'efectivo', importe: '', descripcion: '' })
  showMovimiento.value = true
}

function closeMovimiento() {
  showMovimiento.value = false
}

async function submitMovimiento() {
  try {
    await caja.createMovimiento({
      caja: cajaHoy.value.id,
      tipo: movimientoForm.tipo,
      medio: movimientoForm.medio,
      importe: movimientoForm.importe,
      descripcion: movimientoForm.descripcion,
    })
    closeMovimiento()
    toast.success('Movimiento registrado.')
  } catch (err) {
    toast.error(err.message || 'No se pudo registrar el movimiento.')
  }
}

function openCerrar() {
  cierreForm.total_contado = Number(cajaTotales.value.total || 0).toFixed(2)
  showCerrar.value = true
}

async function submitCerrar() {
  try {
    await caja.cerrarCaja(cierreForm.total_contado)
    showCerrar.value = false
    toast.success('Caja cerrada.')
  } catch (err) {
    toast.error(err.message || 'No se pudo cerrar la caja.')
  }
}

function printCajaResumen() {
  window.print()
}

onMounted(() => {
  caja.loadCajaHoy()
})
</script>
