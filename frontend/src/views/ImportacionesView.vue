<template>
  <section class="imports-screen">
    <header class="imports-header">
      <div>
        <p class="eyebrow">Administración</p>
        <h1>Cargar información</h1>
        <p>Importá alumnos, carreras y cursos desde una plantilla o desde tus archivos Excel actuales.</p>
      </div>
      <DocumentArrowUpIcon class="imports-header-icon" aria-hidden="true" />
    </header>

    <section class="imports-card">
      <div class="imports-card-heading">
        <div>
          <h2>Importar archivo</h2>
          <p>Se aceptan archivos <strong>.xlsx</strong> y <strong>.csv</strong>. La carga es segura y actualiza registros existentes por DNI o legajo.</p>
        </div>
      </div>

      <div class="imports-fields">
        <label>
          <span>Sucursal por defecto</span>
          <select v-model="selectedBranch">
            <option v-for="branch in branches" :key="branch.codigo" :value="branch.codigo">
              {{ branch.nombre }} ({{ branch.codigo }})
            </option>
          </select>
        </label>
        <label>
          <span>Carrera/curso por defecto <small>(opcional)</small></span>
          <input v-model="defaultCareer" type="text" placeholder="Solo necesario si el archivo no lo indica" />
        </label>
      </div>

      <label class="imports-file-field">
        <span>Archivo a cargar</span>
        <input type="file" accept=".xlsx,.csv" @change="onFileChange" />
        <small>{{ selectedFileName || 'Todavía no seleccionaste un archivo.' }}</small>
      </label>

      <div class="imports-actions">
        <button type="button" class="secondary-button" :disabled="loading" @click="downloadTemplate('alumnos')">
          Descargar plantilla de alumnos
        </button>
        <button type="button" class="secondary-button" :disabled="loading" @click="downloadTemplate('carreras')">
          Descargar plantilla de carreras
        </button>
        <button type="button" class="primary-button" :disabled="loading || !selectedFile" @click="submitImport">
          {{ loading ? 'Procesando…' : 'Cargar archivo' }}
        </button>
      </div>

      <p class="imports-hint">
        Las plantillas descargadas son CSV UTF-8 y se abren directamente con Excel. En alumnos, `apellido`, `nombre`, `dni` y `sucursal_codigo` son las columnas principales.
      </p>
    </section>

    <section v-if="error" class="imports-result imports-result-error" role="alert">
      <strong>No se pudo completar la carga.</strong>
      <span>{{ error }}</span>
    </section>

    <section v-if="result" class="imports-card imports-result" aria-live="polite">
      <div class="imports-result-heading">
        <div>
          <p class="eyebrow">Resultado</p>
          <h2>{{ result.archivo }}</h2>
        </div>
        <CheckCircleIcon class="imports-success-icon" aria-hidden="true" />
      </div>
      <div class="imports-summary-grid">
        <article><span>Carreras creadas</span><strong>{{ result.carreras.created }}</strong></article>
        <article><span>Carreras actualizadas</span><strong>{{ result.carreras.updated }}</strong></article>
        <article><span>Alumnos creados</span><strong>{{ result.alumnos.created }}</strong></article>
        <article><span>Alumnos actualizados</span><strong>{{ result.alumnos.updated }}</strong></article>
      </div>
      <div v-if="result.advertencias?.length" class="imports-warnings">
        <h3>Advertencias ({{ result.total_advertencias }})</h3>
        <ul>
          <li v-for="warning in result.advertencias.slice(0, 12)" :key="warning">{{ warning }}</li>
        </ul>
        <small v-if="result.total_advertencias > 12">Se muestran las primeras 12 advertencias.</small>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { CheckCircleIcon, DocumentArrowUpIcon } from '@heroicons/vue/24/outline'
import { apiRequest, downloadFile, uploadFile } from '@/lib/api'

const branches = ref([])
const selectedBranch = ref('POS')
const defaultCareer = ref('')
const selectedFile = ref(null)
const loading = ref(false)
const error = ref('')
const result = ref(null)

const selectedFileName = computed(() => selectedFile.value?.name || '')

onMounted(async () => {
  try {
    const payload = await apiRequest('/sucursales/')
    branches.value = payload.results || payload
    if (branches.value.length && !branches.value.some((branch) => branch.codigo === selectedBranch.value)) {
      selectedBranch.value = branches.value[0].codigo
    }
  } catch {
    branches.value = [{ codigo: 'POS', nombre: 'Posadas' }]
  }
})

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null
  error.value = ''
  result.value = null
}

async function submitImport() {
  if (!selectedFile.value) return
  loading.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await uploadFile('/importaciones/workbook/', selectedFile.value, {
      sucursal: selectedBranch.value,
      carrera: defaultCareer.value,
    })
  } catch (err) {
    error.value = err.message || 'No se pudo importar el archivo.'
  } finally {
    loading.value = false
  }
}

async function downloadTemplate(kind) {
  try {
    const blob = await downloadFile(`/importaciones/plantillas/${kind}/`)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `plantilla_ipac_${kind}.csv`
    link.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    error.value = err.message || 'No se pudo descargar la plantilla.'
  }
}
</script>

<style scoped>
.imports-screen { display: grid; gap: 1.25rem; max-width: 980px; margin: 0 auto; padding: 1.5rem; }
.imports-header, .imports-card, .imports-result { border: 1px solid var(--color-border, #d8dee8); border-radius: 1rem; background: var(--color-surface, #fff); padding: 1.5rem; }
.imports-header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.imports-header h1, .imports-card h2, .imports-result h2 { margin: .2rem 0 .45rem; }
.imports-header p, .imports-card p { margin: 0; color: var(--color-text-secondary, #64748b); }
.imports-header-icon, .imports-success-icon { width: 2.5rem; height: 2.5rem; color: var(--color-primary, #1261a0); flex: 0 0 auto; }
.imports-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-top: 1.25rem; }
.imports-fields label, .imports-file-field { display: grid; gap: .45rem; font-weight: 600; }
.imports-fields span, .imports-file-field span { color: var(--color-text-primary, #1f2937); }
.imports-fields small { font-weight: 400; color: var(--color-text-secondary, #64748b); }
.imports-fields input, .imports-fields select, .imports-file-field input { border: 1px solid var(--color-border, #cbd5e1); border-radius: .65rem; padding: .7rem .8rem; background: var(--color-surface, #fff); }
.imports-file-field { margin-top: 1rem; }
.imports-file-field small, .imports-hint { color: var(--color-text-secondary, #64748b); font-weight: 400; }
.imports-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: .65rem; margin-top: 1.25rem; }
.imports-actions button { border: 0; border-radius: .65rem; padding: .7rem 1rem; cursor: pointer; font-weight: 700; }
.primary-button { background: var(--color-primary, #1261a0); color: white; }
.secondary-button { background: var(--color-surface-muted, #edf2f7); color: var(--color-text-primary, #1f2937); }
.imports-actions button:disabled { cursor: not-allowed; opacity: .55; }
.imports-hint { margin-top: 1rem !important; font-size: .9rem; }
.imports-result-error { display: grid; gap: .35rem; color: #9f1239; background: #fff1f2; }
.imports-result-heading { display: flex; justify-content: space-between; gap: 1rem; }
.imports-summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .75rem; margin-top: 1.25rem; }
.imports-summary-grid article { display: grid; gap: .35rem; border-radius: .75rem; padding: .9rem; background: var(--color-surface-muted, #f1f5f9); }
.imports-summary-grid span { color: var(--color-text-secondary, #64748b); font-size: .85rem; }
.imports-summary-grid strong { font-size: 1.45rem; }
.imports-warnings { margin-top: 1.25rem; border-top: 1px solid var(--color-border, #d8dee8); padding-top: 1rem; }
.imports-warnings h3 { margin: 0 0 .5rem; }
.imports-warnings ul { display: grid; gap: .35rem; margin: 0; padding-left: 1.2rem; color: #92400e; }
@media (max-width: 720px) {
  .imports-screen { padding: 1rem; }
  .imports-fields, .imports-summary-grid { grid-template-columns: 1fr; }
  .imports-actions { justify-content: stretch; }
  .imports-actions button { width: 100%; }
}
</style>
