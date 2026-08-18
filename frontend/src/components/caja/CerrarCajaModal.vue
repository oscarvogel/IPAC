<template>
  <Teleport to="body">
    <div class="modal-backdrop" @click.self="requestClose">
      <form
        v-focus-trap="{ close: requestClose, busy: loading }"
        v-form-validation
        class="modal-card compact-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cerrar-caja-title"
        :aria-busy="loading"
        @submit.prevent="submit"
      >
        <header class="modal-head">
          <div>
            <p class="eyebrow">Cierre de caja</p>
            <h2 id="cerrar-caja-title">Cerrar caja del día</h2>
            <span>Total esperado: $ {{ formatMoney(totalEsperado) }}</span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar formulario" @click="requestClose">
            <XMarkIcon aria-hidden="true" />
          </button>
        </header>
        <section class="modal-section">
          <div class="modal-grid">
            <label>Total contado<input v-model.number="totalContado" type="number" step="0.01" required /></label>
          </div>
        </section>
        <footer class="modal-actions">
          <button class="secondary-button" type="button" :disabled="loading" @click="requestClose">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="loading" type="submit">
            <AppButtonContent :loading="loading" label="Cerrar caja" loading-label="Cerrando" />
          </button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import { formatDate, formatMoney } from '@/lib/formatters'
import { confirmCierreCaja } from '@/lib/swal'
import AppButtonContent from '@/components/ui/AppButtonContent.vue'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'

const props = defineProps({
  totalEsperado: { type: Number, default: 0 },
  cajaHoy: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'submit'])
const totalContado = ref(Number(props.totalEsperado || 0).toFixed(2))

function requestClose() {
  if (!props.loading) emit('close')
}

watch(
  () => props.totalEsperado,
  (next) => {
    if (totalContado.value === '' || totalContado.value == null) {
      totalContado.value = Number(next || 0).toFixed(2)
    }
  },
)

async function submit() {
  const contado = Number(totalContado.value || 0)
  const diferencia = contado - Number(props.totalEsperado || 0)
  const confirmation = await confirmCierreCaja({
    sucursal: props.cajaHoy?.sucursal_nombre || 'Sin sucursal',
    fecha: props.cajaHoy?.fecha ? formatDate(props.cajaHoy.fecha) : 'Sin fecha',
    totalEsperado: props.totalEsperado,
    totalContado: contado,
    diferencia,
  })
  if (confirmation.isConfirmed) emit('submit', totalContado.value)
}
</script>
