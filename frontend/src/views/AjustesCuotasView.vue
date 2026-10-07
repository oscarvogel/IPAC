<template>
  <section class="adjustments-view">
    <header class="audit-header"><div><p class="eyebrow">Configuración · Cobranzas</p><h1>Descuentos y recargos</h1><p>Reglas trazables que se aplican al importe de las cuotas.</p></div><RouterLink to="/configuracion" class="audit-back">Volver a configuración</RouterLink></header>

    <AppPageState v-if="loading || error" :loading="loading" :error="error" label="los ajustes de cuotas" @retry="load" />
    <template v-else>
      <div class="adjustment-grid">
        <section class="adjustment-card">
          <header><div><p class="eyebrow">Beneficios y excepciones</p><h2>Tipos de descuento</h2></div></header>
          <form v-form-validation class="adjustment-form" @submit.prevent="createDiscount">
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
          <form v-form-validation class="adjustment-form" @submit.prevent="createRule">
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

        <section class="adjustment-card adjustment-card--wide">
          <header><div><p class="eyebrow">Mora por mes</p><h2>Interés de las cuotas</h2><p class="card-hint">La tasa mensual se parametriza por vigencia: se cargan varias y cada cuota usa la que estaba vigente ese día.</p></div></header>
          <form v-form-validation class="adjustment-form" @submit.prevent="createRate">
            <label>Sucursal<select v-model="rate.sucursal" required><option value="">Seleccionar</option><option v-for="branch in sucursales" :key="branch.id" :value="branch.id">{{ branch.nombre }}</option></select></label>
            <label>Tasa mensual (%)<input v-model="rate.porcentaje_mensual" type="number" min="0" step="0.001" required placeholder="Ej. 5.5" /></label>
            <label>Vigencia desde<input v-model="rate.vigencia_desde" type="date" required /></label>
            <label>Vigencia hasta<input v-model="rate.vigencia_hasta" type="date" /></label>
            <label>Cuenta el interés desde<select v-model="rate.base_calculo"><option value="dia_1_del_mes">Día 1 del mes de la cuota</option><option value="fecha_vencimiento">Fecha de vencimiento</option></select></label>
            <label>Aplica la tasa por<select v-model="rate.unidad_calculo"><option value="meses">Meses completos</option><option value="dias">Días prorrateados (30 por mes)</option></select></label>
            <label class="adjustment-form--wide">Descripción<input v-model.trim="rate.descripcion" maxlength="160" placeholder="Ej. Tasa acordada con el contador" /></label>
            <button type="submit">Crear tasa de interés</button>
          </form>
          <ul class="adjustment-list"><li v-for="item in rates" :key="item.id"><span><strong>{{ Number(item.porcentaje_mensual).toLocaleString('es-AR') }}% mensual</strong><small>{{ item.sucursal_nombre }} · desde {{ formatDate(item.vigencia_desde) }}<template v-if="item.vigencia_hasta"> hasta {{ formatDate(item.vigencia_hasta) }}</template> · {{ BASE_LABELS[item.base_calculo] }} · {{ UNIDAD_LABELS[item.unidad_calculo] }}</small></span><button @click="toggle('/tasas-interes/', item, 'activa')">{{ item.activa ? 'Desactivar' : 'Activar' }}</button></li></ul>

          <div class="projection">
            <div class="projection-controls">
              <label>Fecha de evaluación<input v-model="proyeccion.fecha_evaluacion" type="date" /></label>
              <button type="button" :disabled="proyectando" @click="proyectar">{{ proyectando ? 'Calculando…' : 'Proyectar interés' }}</button>
            </div>
            <p v-if="proyeccionError" class="projection-message is-error" role="alert">{{ proyeccionError }}</p>
            <div v-else-if="proyeccionResult" class="projection-result">
              <dl class="projection-metrics">
                <div><dt>Interés total</dt><dd>{{ money(proyeccionResult.total_interes) }}</dd></div>
                <div><dt>Cuotas evaluadas</dt><dd>{{ proyeccionResult.cuotas_evaluadas }}</dd></div>
                <div><dt>Cuotas con interés</dt><dd>{{ proyeccionResult.cuotas_con_interes }}</dd></div>
              </dl>
              <p v-if="proyeccionResult.sin_tasa.length" class="projection-message is-warning" role="status">{{ sinTasaMessage(proyeccionResult.sin_tasa.length) }}</p>
              <p v-if="!proyeccionResult.detalle.length" class="projection-message">No hay cuotas con saldo para esa fecha.</p>
              <table v-else class="projection-table">
                <caption class="sr-only">Detalle del interés proyectado por cuota</caption>
                <thead><tr><th scope="col">Cuota</th><th scope="col">Saldo pendiente</th><th scope="col">Días</th><th scope="col">Períodos</th><th scope="col">Interés</th></tr></thead>
                <tbody><tr v-for="row in proyeccionResult.detalle" :key="row.cuota_id"><td>#{{ row.cuota_id }}</td><td>{{ money(row.saldo_pendiente) }}</td><td>{{ row.dias_interesables }}</td><td>{{ row.periodos }}</td><td>{{ money(row.importe) }}</td></tr></tbody>
              </table>
            </div>
          </div>
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
import { vFormValidation } from '@/directives/accessibility'

const { sucursales, conceptos, loadCatalogo, loadCatalogos } = useCatalogos()
const toast = useToast()
const discounts = ref([])
const rules = ref([])
const rates = ref([])
const loading = ref(false)
const error = ref('')
const proyectando = ref(false)
const proyeccionResult = ref(null)
const proyeccionError = ref('')
const discount = reactive({ nombre: '', sucursal: '', modalidad: 'porcentaje', valor: '' })
const rule = reactive({ nombre: '', sucursal: '', concepto: '', modalidad: 'porcentaje', valor: '', dias_tolerancia: 0 })
const rate = reactive({ sucursal: '', porcentaje_mensual: '', vigencia_desde: '', vigencia_hasta: '', base_calculo: 'dia_1_del_mes', unidad_calculo: 'meses', descripcion: '' })
const proyeccion = reactive({ fecha_evaluacion: todayIso() })
const ruleConcepts = computed(() => conceptos.value.filter((item) => String(item.sucursal) === String(rule.sucursal)))

//: Las etiquetas vienen del backend, pero la pantalla las repite para no dejar
//: la columna en blanco si un valor llegara sin traducción.
const BASE_LABELS = { dia_1_del_mes: 'desde el día 1 del mes', fecha_vencimiento: 'desde el vencimiento' }
const UNIDAD_LABELS = { meses: 'meses completos', dias: 'días prorrateados' }

function todayIso() {
  const ahora = new Date()
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${ahora.getFullYear()}-${mes}-${dia}`
}

function formatDate(valor) {
  if (!valor) return ''
  const [anio, mes, dia] = String(valor).split('-')
  return `${dia}/${mes}/${anio}`
}

function money(valor) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(Number(valor))
}

// "1 cuota quedó afuera" y no "1 cuotas": el contador va adelante de un texto
// pluralizado y se lee todas las veces que se proyecta.
function sinTasaMessage(cantidad) {
  return cantidad === 1
    ? '1 cuota quedó afuera porque su sucursal no tiene tasa cargada.'
    : `${cantidad} cuotas quedaron afuera porque su sucursal no tiene tasa cargada.`
}

async function load() {
  loading.value = true; error.value = ''
  try {
    await Promise.all([
      loadCatalogo?.('sucursales') || loadCatalogos(),
      loadCatalogo?.('conceptos') || loadCatalogos(),
    ])
    const [discountData, ruleData, rateData] = await Promise.all([
      apiRequest('/tipos-descuento/'),
      apiRequest('/reglas-recargo/'),
      apiRequest('/tasas-interes/'),
    ])
    discounts.value = discountData.results || []
    rules.value = ruleData.results || []
    rates.value = rateData.results || []
  } catch (err) { error.value = err.message || 'No se pudieron cargar los ajustes.' } finally { loading.value = false }
}

async function createDiscount() {
  try { await apiRequest('/tipos-descuento/', { method: 'POST', body: discount }); Object.assign(discount, { nombre: '', sucursal: '', modalidad: 'porcentaje', valor: '' }); await load(); toast.success('Tipo de descuento creado') } catch (err) { toast.error(err.message) }
}
async function createRule() {
  try { await apiRequest('/reglas-recargo/', { method: 'POST', body: { ...rule, concepto: rule.concepto || null } }); Object.assign(rule, { nombre: '', sucursal: '', concepto: '', modalidad: 'porcentaje', valor: '', dias_tolerancia: 0 }); await load(); toast.success('Regla de recargo creada') } catch (err) { toast.error(err.message) }
}
async function createRate() {
  try {
    await apiRequest('/tasas-interes/', { method: 'POST', body: { ...rate, vigencia_hasta: rate.vigencia_hasta || null } })
    Object.assign(rate, { sucursal: '', porcentaje_mensual: '', vigencia_desde: '', vigencia_hasta: '', base_calculo: 'dia_1_del_mes', unidad_calculo: 'meses', descripcion: '' })
    await load()
    toast.success('Tasa de interés creada')
  } catch (err) { toast.error(err.message) }
}

// La proyección no escribe nada: sólo informa cuánto interés habría a esa
// fecha. El mensaje de error va en línea y no en un toast, porque sin tasa
// cargada es el estado normal de una instalación nueva, no un fallo.
async function proyectar() {
  proyectando.value = true; proyeccionError.value = ''
  try {
    proyeccionResult.value = await apiRequest('/tasas-interes/proyectar/', { query: { fecha_evaluacion: proyeccion.fecha_evaluacion } })
  } catch (err) {
    proyeccionResult.value = null
    proyeccionError.value = err.message
  } finally { proyectando.value = false }
}

// El campo del toggle no es el mismo en todos los modelos: TipoDescuento y
// ReglaRecargo usan `activo`, TasaInteres usa `activa`. Mandar el nombre
// equivocado no da error: el serializer lo ignora y el botón no hace nada.
async function toggle(base, item, campo = 'activo') { try { await apiRequest(`${base}${item.id}/`, { method: 'PATCH', body: { [campo]: !item[campo] } }); await load() } catch (err) { toast.error(err.message) } }
async function recalculate() { try { const result = await apiRequest('/reglas-recargo/recalcular/', { method: 'POST', body: {} }); toast.success(`${result.actualizadas} cuotas actualizadas`) } catch (err) { toast.error(err.message) } }
function adjustmentValue(item) { return item.modalidad === 'porcentaje' ? `${Number(item.valor)}%` : money(item.valor) }
onMounted(load)
</script>

<style scoped>
.adjustments-view { display: grid; gap: 1.25rem; }.adjustment-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }.adjustment-card { padding: 1rem; border: 1px solid var(--border); border-radius: 1rem; background: var(--surface); }.adjustment-card h2 { margin: .2rem 0 1rem; }.card-hint { margin: 0 0 .9rem; color: var(--text-secondary); font-size: .78rem; }.adjustment-card--wide { grid-column: 1 / -1; }.adjustment-form { display: grid; grid-template-columns: 1fr 1fr; gap: .7rem; }.adjustment-form label { display: grid; gap: .3rem; color: var(--text-secondary); font-size: .78rem; font-weight: 700; }.adjustment-form--wide { grid-column: 1 / -1; }.adjustment-form input,.adjustment-form select { min-height: 2.55rem; border: 1px solid var(--border); border-radius: .6rem; padding: .5rem .65rem; background: var(--surface); color: var(--text-primary); }.adjustment-form button,.recalculate-action,.projection-controls button { min-height: 2.55rem; border: 0; border-radius: .6rem; padding: 0 .8rem; background: var(--primary); color: var(--on-primary); font-weight: 800; }.adjustment-form button { grid-column: 1 / -1; }.adjustment-form button:disabled,.projection-controls button:disabled { opacity: .6; cursor: progress; }.recalculate-action { width: 100%; margin-top: .7rem; background: var(--success); }.adjustment-list { display: grid; gap: 0; margin: 1rem 0 0; padding: 0; list-style: none; }.adjustment-list li { display: flex; justify-content: space-between; align-items: center; gap: .6rem; padding: .75rem 0; border-top: 1px solid var(--border); }.adjustment-list span { display: grid; gap: .2rem; }.adjustment-list small { color: var(--text-secondary); }.adjustment-list button { border: 1px solid var(--border); border-radius: .5rem; padding: .45rem .6rem; background: var(--surface); color: var(--primary); font-weight: 700; }
.projection { margin-top: 1.2rem; padding-top: 1rem; border-top: 1px solid var(--border); }.projection-controls { display: flex; flex-wrap: wrap; align-items: end; gap: .7rem; }.projection-controls label { display: grid; gap: .3rem; color: var(--text-secondary); font-size: .78rem; font-weight: 700; }.projection-controls input { min-height: 2.55rem; border: 1px solid var(--border); border-radius: .6rem; padding: .5rem .65rem; background: var(--surface); color: var(--text-primary); }.projection-controls button { background: var(--success); }.projection-message { margin: .9rem 0 0; padding: .7rem .8rem; border-radius: .6rem; font-size: .82rem; background: var(--surface-alt, var(--surface)); border: 1px solid var(--border); }.projection-message.is-error { border-color: var(--danger); color: var(--danger); }.projection-message.is-warning { border-color: var(--warning); }.projection-metrics { display: flex; flex-wrap: wrap; gap: 1.5rem; margin: 1rem 0 0; }.projection-metrics div { display: grid; gap: .15rem; }.projection-metrics dt { color: var(--text-secondary); font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }.projection-metrics dd { margin: 0; font-size: 1.25rem; font-weight: 800; }.projection-table { width: 100%; margin-top: .9rem; border-collapse: collapse; font-size: .82rem; }.projection-table th,.projection-table td { padding: .55rem .6rem; border-bottom: 1px solid var(--border); text-align: left; }.projection-table th { color: var(--text-secondary); font-size: .72rem; text-transform: uppercase; letter-spacing: .04em; }
@media(max-width:900px){.adjustment-grid{grid-template-columns:1fr}}@media(max-width:480px){.adjustment-form{grid-template-columns:1fr}.adjustment-form button{grid-column:auto}.adjustment-form--wide{grid-column:auto}.projection-controls{flex-direction:column;align-items:stretch}}
</style>
