<template>
  <Teleport to="body">
    <div class="modal-backdrop" @click.self="$emit('close')">
      <form class="modal-card compact-modal" @submit.prevent="submit">
        <header class="modal-head">
          <div>
            <p class="eyebrow">Movimiento de caja</p>
            <h2>Registrar {{ form.tipo }}</h2>
            <span>Caja {{ cajaHoy?.sucursal_nombre }} · {{ cajaHoy?.fecha }}</span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar" @click="$emit('close')">
            <XMarkIcon aria-hidden="true" />
          </button>
        </header>
        <section class="modal-section">
          <div class="modal-grid">
            <label>
              Tipo
              <select v-model="form.tipo">
                <option value="ingreso">Ingreso</option>
                <option value="egreso">Egreso</option>
                <option value="retiro">Retiro</option>
                <option value="pase">Pase</option>
              </select>
            </label>
            <label>
              Medio
              <select v-model="form.medio">
                <option value="efectivo">Efectivo</option>
                <option value="transferencia">Transferencia</option>
                <option value="tarjeta">Tarjeta</option>
                <option value="otro">Otro</option>
              </select>
            </label>
            <label>Importe<input v-model.number="form.importe" type="number" min="0" step="0.01" required /></label>
            <label>Descripcion<input v-model="form.descripcion" required /></label>
          </div>
        </section>
        <footer class="modal-actions">
          <button class="secondary-button" type="button" @click="$emit('close')">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="loading" type="submit">Guardar movimiento</button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  cajaHoy: { type: Object, required: true },
  loading: { type: Boolean, default: false },
  tipoInicial: { type: String, default: 'egreso' },
})

const emit = defineEmits(['close', 'submit'])

const form = reactive({
  tipo: props.tipoInicial,
  medio: 'efectivo',
  importe: '',
  descripcion: '',
})

function submit() {
  emit('submit', {
    caja: props.cajaHoy.id,
    tipo: form.tipo,
    medio: form.medio,
    importe: form.importe,
    descripcion: form.descripcion,
  })
}
</script>
