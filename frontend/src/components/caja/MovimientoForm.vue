<template>
  <Teleport to="body">
    <AppModalTransition :open="open">
      <div class="modal-backdrop" @click.self="requestClose">
      <form
        v-focus-trap="{ close: requestClose, busy: loading }"
        v-form-validation
        class="modal-card compact-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="movimiento-form-title"
        :aria-busy="loading"
        @submit.prevent="submit"
      >
        <header class="modal-head">
          <div>
            <p class="eyebrow">Movimiento de caja</p>
            <h2 id="movimiento-form-title">Registrar {{ form.tipo }}</h2>
            <span>Caja {{ cajaHoy?.sucursal_nombre }} · {{ cajaHoy?.fecha }}</span>
          </div>
          <button class="icon-button" type="button" aria-label="Cerrar formulario" @click="requestClose">
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
                <option value="mercado_pago">Mercado Pago</option>
                <option value="tarjeta">Tarjeta</option>
                <option value="otro">Otro</option>
              </select>
            </label>
            <label>Importe<input v-model.number="form.importe" type="number" min="0" step="0.01" required /></label>
            <label>Descripcion<input v-model="form.descripcion" required /></label>
            <label v-if="requiereConformidad">
              Recibe el dinero
              <select v-model="form.recibido_por" required>
                <option value="">Seleccionar quien recibe</option>
                <option v-for="persona in receptores" :key="persona.id" :value="persona.id">
                  {{ persona.username }} - {{ persona.rol_label }}
                </option>
              </select>
            </label>
          </div>
        </section>
        <footer class="modal-actions">
          <button class="secondary-button" type="button" :disabled="loading" @click="requestClose">Cancelar</button>
          <button class="primary-button modal-submit" :disabled="loading" type="submit">
            <AppButtonContent :loading="loading" label="Guardar movimiento" loading-label="Guardando…" />
          </button>
        </footer>
      </form>
      </div>
    </AppModalTransition>
  </Teleport>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import AppButtonContent from '@/components/ui/AppButtonContent.vue'
import AppModalTransition from '@/components/ui/AppModalTransition.vue'
import { vFocusTrap, vFormValidation } from '@/directives/accessibility'

// El pase y el retiro exigen saber quien recibe el dinero: sin esa conformidad
// el comprobante no queda auditable.
const TIPOS_CON_COMPROBANTE = ['pase', 'retiro']

const props = defineProps({
  open: { type: Boolean, default: false },
  cajaHoy: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  tipoInicial: { type: String, default: 'egreso' },
  receptores: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'submit'])

const form = reactive({
  tipo: props.tipoInicial,
  medio: 'efectivo',
  importe: '',
  descripcion: '',
  recibido_por: '',
})

const requiereConformidad = computed(() => TIPOS_CON_COMPROBANTE.includes(form.tipo))

watch(
  () => props.open,
  (open) => {
    if (!open) return
    form.tipo = props.tipoInicial
    form.medio = 'efectivo'
    form.importe = ''
    form.descripcion = ''
    form.recibido_por = ''
  },
)

function requestClose() {
  if (!props.loading) emit('close')
}

function submit() {
  emit('submit', {
    caja: props.cajaHoy.id,
    tipo: form.tipo,
    medio: form.medio,
    importe: form.importe,
    descripcion: form.descripcion,
    recibido_por: requiereConformidad.value && form.recibido_por ? Number(form.recibido_por) : null,
  })
}
</script>
