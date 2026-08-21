<template>
  <section class="adjustments-view">
    <header class="audit-header"><div><p class="eyebrow">Configuración · Cobranzas</p><h1>Descuentos y recargos</h1><p>Reglas trazables que se aplican al importe de las cuotas.</p></div><RouterLink to="/configuracion" class="audit-back">Volver a configuración</RouterLink></header>

    <AppPageState v-if="loading || error" :loading="loading" :error="error" label="los ajustes de cuotas" @retry="load" />
    <template v-else>
      <div class="adjustment-grid">
        <section class="adjustment-card">
          <header><div><p class="eyebrow">Beneficios y excepciones</p><h2>Tipos de descuento</h2></div></header>
          <form class="adjustment-form" @submit.prevent="createDiscount">
            <label>Nombre<input v-model.trim="discount.nombre" required placeholder="Ej. Beca" /></label>
            <label>Sucursal<select v-model="discount.sucursal" required><option value="">Seleccionar</option><option v-for="branch in sucursales" :key="branch.id" :value="branch.id">{{ branch.nombre }}</option></select></label>
            <label>Modalidad<select v-model="discount.modalidad"><option value="porcentaje">Porcentaje</option><option value="importe">Importe fijo</option></select></label>
            <label>Valor<input v-model="discount.valor" type="number" min="0" step="0.01" required /></label>
            <button type="submit">Crear tipo de descuento</button>
          </form>
          <ul class="adjustment-list"><li v-for="item in discounts" :key="item.id"><span><strong>{{ item.nombre }}</strong><small>{{ item.sucursal_nombre }} · {{ adjustmentValue(item) }}</small></span><button @click="toggle('/tipos-descuento/', item)">{{ item.activo ? 'Desactivar' : 'Activar' }}</button></li></ul>
        </section>

        <section class="adjustment-card">
          <header><div><p class="eyebrow">Mora por vencimiento</p><h2>Reglas de recargo</h2></div></header>
          <form class="adjustment-form" @submit.prevent="createRule">
            <label>Nombre<input v-model.trim="rule.nombre" required placeholder="Ej. Mora mensual" /></label>
            <label>Sucursal<select v-model="rule.sucursal" required><option value="">Seleccionar</option><option v-for="branch in sucursales" :key="branch.id" :value="branch.id">{{ branch.nombre }}</option></select></label>
            <label>Concepto<select v-model="rule.concepto"><option value="">Todos los conceptos</option><option v-for="concept in ruleConcepts" :key="concept.id" :value="concept.id">{{ concept.nombre }}</option></select></label>
            <label>Días de tolerancia<input v-model="rule.dias_tolerancia" type="number" min="0" required /></label>
            <label>Modalidad<select v-model="rule.modalidad"><option value="porcentaje">Porcentaje</option><option value="importe">Importe fijo</option></select></label>
            <label>Valor<input v-model="rule.valor" type="number" min="0" step="0.01" required /></label>
            <button type="submit">Crear regla de recargo</button>
          </form>
          <button class="recalculate-action" @click="recalculate">Recalcular cuotas vencidas</button>
          <ul class="adjustment-list"><li v-for="item in rules" :key="item.id"><span><strong>{{ item.nombre }}</strong><small>{{ item.sucursal_nombre }} · {{ item.concepto_nombre || 'Todos los conceptos' }} · {{ adjustmentValue(item) }} después de {{ item.dias_tolerancia }} días</small></span><button @click="toggle('/reglas-recargo/', item)">{{ item.activo ? 'Desactivar' : 'Activar' }}</button></li></ul>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { apiRequest } from '@/lib/api'
import { useCatalogos } from '@/composables/useCatalogos'
import { useToast } from '@/composables/useToast'
import AppPageState from '@/components/ui/AppPageState.vue'

const { sucursales, conceptos, loadCatalogos } = useCatalogos()
const toast = useToast()
const discounts = ref([])
const rules = ref([])
const loading = ref(false)
const error = ref('')
const discount = reactive({ nombre: '', sucursal: '', modalidad: 'porcentaje', valor: '' })
const rule = reactive({ nombre: '', sucursal: '', concepto: '', modalidad: 'porcentaje', valor: '', dias_tolerancia: 0 })
const ruleConcepts = computed(() => conceptos.value.filter((item) => String(item.sucursal) === String(rule.sucursal)))

async function load() {
  loading.value = true; error.value = ''
  try {
    await loadCatalogos(true)
    const [discountData, ruleData] = await Promise.all([apiRequest('/tipos-descuento/'), apiRequest('/reglas-recargo/')])
    discounts.value = discountData.results || []
    rules.value = ruleData.results || []
  } catch (err) { error.value = err.message || 'No se pudieron cargar los ajustes.' } finally { loading.value = false }
}

async function createDiscount() {
  try { await apiRequest('/tipos-descuento/', { method: 'POST', body: discount }); Object.assign(discount, { nombre: '', sucursal: '', modalidad: 'porcentaje', valor: '' }); await load(); toast.success('Tipo de descuento creado') } catch (err) { toast.error(err.message) }
}
async function createRule() {
  try { await apiRequest('/reglas-recargo/', { method: 'POST', body: { ...rule, concepto: rule.concepto || null } }); Object.assign(rule, { nombre: '', sucursal: '', concepto: '', modalidad: 'porcentaje', valor: '', dias_tolerancia: 0 }); await load(); toast.success('Regla de recargo creada') } catch (err) { toast.error(err.message) }
}
async function toggle(base, item) { try { await apiRequest(`${base}${item.id}/`, { method: 'PATCH', body: { activo: !item.activo } }); await load() } catch (err) { toast.error(err.message) } }
async function recalculate() { try { const result = await apiRequest('/reglas-recargo/recalcular/', { method: 'POST', body: {} }); toast.success(`${result.actualizadas} cuotas actualizadas`) } catch (err) { toast.error(err.message) } }
function adjustmentValue(item) { return item.modalidad === 'porcentaje' ? `${Number(item.valor)}%` : new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(Number(item.valor)) }
onMounted(load)
</script>

<style scoped>
.adjustments-view { display: grid; gap: 1.25rem; }.adjustment-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }.adjustment-card { padding: 1rem; border: 1px solid var(--border); border-radius: 1rem; background: var(--surface); }.adjustment-card h2 { margin: .2rem 0 1rem; }.adjustment-form { display: grid; grid-template-columns: 1fr 1fr; gap: .7rem; }.adjustment-form label { display: grid; gap: .3rem; color: var(--text-secondary); font-size: .78rem; font-weight: 700; }.adjustment-form input,.adjustment-form select { min-height: 2.55rem; border: 1px solid var(--border); border-radius: .6rem; padding: .5rem .65rem; background: var(--surface); color: var(--text-primary); }.adjustment-form button,.recalculate-action { min-height: 2.55rem; border: 0; border-radius: .6rem; padding: 0 .8rem; background: var(--primary); color: white; font-weight: 800; }.adjustment-form button { grid-column: 1 / -1; }.recalculate-action { width: 100%; margin-top: .7rem; background: var(--success); }.adjustment-list { display: grid; gap: 0; margin: 1rem 0 0; padding: 0; list-style: none; }.adjustment-list li { display: flex; justify-content: space-between; align-items: center; gap: .6rem; padding: .75rem 0; border-top: 1px solid var(--border); }.adjustment-list span { display: grid; gap: .2rem; }.adjustment-list small { color: var(--text-secondary); }.adjustment-list button { border: 1px solid var(--border); border-radius: .5rem; padding: .45rem .6rem; background: var(--surface); color: var(--primary); font-weight: 700; }
@media(max-width:900px){.adjustment-grid{grid-template-columns:1fr}}@media(max-width:480px){.adjustment-form{grid-template-columns:1fr}.adjustment-form button{grid-column:auto}}
</style>
