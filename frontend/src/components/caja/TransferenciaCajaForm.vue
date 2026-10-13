<template>
  <section class="transfer-form border-border bg-surface" aria-labelledby="transferencia-form-title">
    <header>
      <p class="eyebrow">Efectivo físico</p>
      <h2 id="transferencia-form-title">Nueva transferencia</h2>
      <p>Seleccioná dos cajas abiertas para hoy. El destino recibe el efectivo al confirmar.</p>
    </header>
    <form novalidate @submit.prevent="review">
      <fieldset :disabled="loading || cajas.length < 2" :aria-describedby="validationError ? 'transferencia-validacion' : undefined">
        <legend class="sr-only">Datos de la transferencia</legend>
        <div class="transfer-fields">
          <label for="transferencia-origen">Caja de origen
            <select id="transferencia-origen" v-model="form.origen_id" required>
              <option value="">Seleccionar origen</option>
              <option v-for="caja in cajas" :key="caja.id" :value="caja.id">{{ cajaLabel(caja) }}</option>
            </select>
          </label>
          <label for="transferencia-destino">Caja de destino
            <select id="transferencia-destino" v-model="form.destino_id" required>
              <option value="">Seleccionar destino</option>
              <option v-for="caja in cajas" :key="caja.id" :value="caja.id" :disabled="String(caja.id) === String(form.origen_id)">{{ cajaLabel(caja) }}</option>
            </select>
          </label>
          <p v-if="origen" class="source-balance">Efectivo esperado en origen: <strong>$ {{ formatMoney(origen.total_esperado, { fractionDigits: 2 }) }}</strong></p>
          <label for="transferencia-importe">Importe en efectivo
            <input id="transferencia-importe" :value="form.importe" type="number" @input="form.importe = $event.target.value" min="0.01" step="0.01" inputmode="decimal" required />
          </label>
          <label for="transferencia-motivo">Motivo
            <input id="transferencia-motivo" v-model="form.motivo" type="text" maxlength="180" required />
          </label>
        </div>
        <p v-if="validationError" id="transferencia-validacion" ref="validationSummary" tabindex="-1" role="alert" class="form-error">{{ validationError }}</p>
        <button class="primary-button" type="submit">Revisar transferencia</button>
      </fieldset>
    </form>
  </section>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { formatMoney } from '@/lib/formatters'

const props = defineProps({ cajas: { type: Array, required: true }, loading: Boolean })
const emit = defineEmits(['review'])
const form = reactive({ origen_id: '', destino_id: '', importe: '', motivo: '' })
const validationError = ref('')
const validationSummary = ref(null)
watch(validationError, async (message) => {
  if (!message) return
  await nextTick()
  validationSummary.value?.focus()
})
const origen = computed(() => props.cajas.find((caja) => String(caja.id) === String(form.origen_id)))

function cajaLabel(caja) {
  return caja.sucursal_nombre + ' · ' + caja.usuario_nombre + ' · Caja #' + caja.id
}

watch(() => form.origen_id, (id) => {
  if (String(form.destino_id) === String(id)) form.destino_id = ''
  validationError.value = ''
})

function review() {
  validationError.value = ''
  if (!form.origen_id || !form.destino_id || !form.importe || !form.motivo.trim()) {
    validationError.value = 'Completá origen, destino, importe y motivo.'
    return
  }
  if (form.motivo.trim().length > 180) {
    validationError.value = 'Usá hasta 180 caracteres para el motivo.'
    return
  }
  if (String(form.origen_id) === String(form.destino_id)) {
    validationError.value = 'Seleccioná cajas distintas para origen y destino.'
    return
  }
  if (!Number.isFinite(Number(form.importe)) || Number(form.importe) <= 0 || !/^\d+(\.\d{1,2})?$/.test(form.importe)) {
    validationError.value = 'Ingresá un importe positivo con hasta dos decimales.'
    return
  }
  emit('review', {
    origen_id: Number(form.origen_id), destino_id: Number(form.destino_id),
    importe: form.importe, motivo: form.motivo.trim(),
  })
}
</script>

<style scoped>
.transfer-form { border: 1px solid; border-radius: 1rem; padding: 1.5rem; }
header p:last-child { color: var(--color-text-secondary); margin: .5rem 0 1.25rem; }
fieldset { border: 0; margin: 0; padding: 0; min-width: 0; }
.transfer-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
label { display: grid; gap: .5rem; font-weight: 600; min-width: 0; }
input, select { width: 100%; min-width: 0; }
.source-balance { grid-column: 1 / -1; margin: 0; font-size: .9rem; }
.primary-button { margin-top: 1.25rem; }
.form-error { color: #b42318; margin-top: 1rem; }
@media (max-width: 640px) { .transfer-fields { grid-template-columns: 1fr; } .transfer-form { padding: 1rem; } }
</style>
