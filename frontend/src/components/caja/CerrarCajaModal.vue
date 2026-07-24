<template>
  <Teleport to="body">
    <div class="modal-backdrop" @click.self="$emit('close')">
      <form class="modal-card compact-modal" @submit.prevent="submit">
        <header class="modal-head">
          <div>
            <p class="eyebrow">Cierre de caja</p>
            <h2>Cerrar caja del dia</h2>
            <span>Total esperado: $ {{ formatMoney(totalEsperado) }}</span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar" @click="$emit('close')">×</button>
        </header>
        <section class="modal-section">
          <div class="modal-grid">
            <label>Total contado<input v-model.number="totalContado" type="number" step="0.01" required /></label>
          </div>
        </section>
        <footer class="modal-actions">
          <button class="secondary-button" type="button" @click="$emit('close')">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="loading" type="submit">Confirmar cierre</button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { formatMoney } from '@/lib/formatters'

const props = defineProps({
  totalEsperado: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'submit'])

const totalContado = ref(Number(props.totalEsperado || 0).toFixed(2))

// Si cambia el total esperado (por un reload de caja), mantenemos el
// valor cargado solo la primera vez; despues el usuario lo edita a mano.
watch(
  () => props.totalEsperado,
  (next) => {
    if (totalContado.value === '' || totalContado.value == null) {
      totalContado.value = Number(next || 0).toFixed(2)
    }
  },
)

function submit() {
  emit('submit', totalContado.value)
}
</script>
