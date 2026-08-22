<template>
  <section class="imports-screen">
    <header class="imports-header">
      <div>
        <p class="eyebrow">Administración</p>
        <h1>Cargar información</h1>
        <p>Importá alumnos, carreras, conceptos y saldos iniciales desde plantillas o archivos Excel.</p>
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

      <div class="imports-file-field">
        <span>Archivo a revisar</span>
        <div class="imports-file-picker">
          <label class="imports-file-button">
            <span>Elegir archivo</span>
            <input type="file" accept=".xlsx,.csv" @change="onFileChange" />
          </label>
          <span class="imports-file-name" aria-live="polite">
            {{ selectedFileName || 'Ningún archivo seleccionado' }}
          </span>
        </div>
        <small>Formatos aceptados: Excel (.xlsx) o CSV (.csv).</small>
      </div>

      <div class="imports-actions">
        <button type="button" class="secondary-button" :disabled="loading" @click="downloadTemplate('alumnos')">
          Descargar plantilla de alumnos
        </button>
        <button type="button" class="secondary-button" :disabled="loading" @click="downloadTemplate('carreras')">
          Descargar plantilla de carreras
        </button>
        <button type="button" class="secondary-button" :disabled="loading" @click="downloadTemplate('conceptos')">
          Descargar plantilla de conceptos
        </button>
        <button type="button" class="secondary-button" :disabled="loading" @click="downloadTemplate('saldos_iniciales')">
          Descargar plantilla de saldos
        </button>
        <button type="button" class="primary-button" :disabled="loading || !selectedFile" @click="reviewImport">
          {{ loading ? 'Analizando…' : 'Revisar importación' }}
        </button>
      </div>

      <p class="imports-hint">
        Las plantillas descargadas son CSV UTF-8 y se abren directamente con Excel. Para importar alumnos, completá apellido, nombre, DNI y código de sucursal.
      </p>
    </section>

    <section v-if="preview" class="imports-card imports-preview" aria-live="polite">
      <div class="imports-result-heading">
        <div>
          <p class="eyebrow">Revisión de importación</p>
          <h2>{{ preview.archivo }}</h2>
        </div>
        <CheckCircleIcon v-if="!hasPreviewErrors" class="imports-success-icon" aria-hidden="true" />
      </div>

      <div class="imports-summary-grid imports-preview-grid">
        <article><span>Alumnos encontrados</span><strong>{{ preview.alumnos?.found || 0 }}</strong></article>
        <article><span>Alumnos nuevos</span><strong>{{ preview.alumnos?.created || 0 }}</strong></article>
        <article><span>Alumnos a actualizar</span><strong>{{ preview.alumnos?.updated || 0 }}</strong></article>
        <article :class="{ 'imports-summary-danger': hasPreviewErrors }"><span>Errores críticos</span><strong>{{ preview.total_errores || 0 }}</strong></article>
        <article><span>Carreras nuevas</span><strong>{{ preview.carreras?.created || 0 }}</strong></article>
        <article><span>Carreras a actualizar</span><strong>{{ preview.carreras?.updated || 0 }}</strong></article>
        <article><span>Conceptos nuevos</span><strong>{{ preview.conceptos?.created || 0 }}</strong></article>
        <article><span>Conceptos a actualizar</span><strong>{{ preview.conceptos?.updated || 0 }}</strong></article>
        <article><span>Saldos iniciales nuevos</span><strong>{{ preview.saldos_iniciales?.created || 0 }}</strong></article>
        <article><span>Saldos ya registrados</span><strong>{{ preview.saldos_iniciales?.updated || 0 }}</strong></article>
        <article><span>Advertencias</span><strong>{{ preview.total_advertencias || 0 }}</strong></article>
      </div>

      <div v-if="hasPreviewErrors" class="imports-preview-block imports-preview-error" role="alert">
        <strong>Corregí los errores críticos antes de confirmar.</strong>
        <ul>
          <li v-for="item in preview.errores?.slice(0, 12)" :key="item">{{ item }}</li>
        </ul>
      </div>

      <div v-if="preview.advertencias?.length" class="imports-preview-block imports-warnings">
        <h3>Advertencias ({{ preview.total_advertencias }})</h3>
        <ul>
          <li v-for="warning in preview.advertencias.slice(0, 12)" :key="warning">{{ warning }}</li>
        </ul>
        <small v-if="preview.total_advertencias > 12">Se muestran las primeras 12 advertencias.</small>
      </div>

      <div class="imports-preview-actions">
        <span v-if="hasPreviewErrors" class="imports-preview-status">La importación no se puede confirmar todavía.</span>
        <button v-else type="button" class="primary-button" :disabled="loading" @click="confirmImport">
          Confirmar importación
        </button>
      </div>
    </section>

    <section v-if="error" class="imports-result imports-result-error" role="alert">
      <strong>No se pudo completar la operación.</strong>
      <span>{{ error }}</span>
    </section>

    <section v-if="result" class="imports-card imports-result" aria-live="polite">
      <div class="imports-result-heading">
        <div>
        <p class="eyebrow">Importación confirmada</p>
          <h2>{{ result.archivo }}</h2>
        </div>
        <CheckCircleIcon class="imports-success-icon" aria-hidden="true" />
      </div>
      <div class="imports-summary-grid">
        <article><span>Carreras creadas</span><strong>{{ result.carreras.created }}</strong></article>
        <article><span>Carreras actualizadas</span><strong>{{ result.carreras.updated }}</strong></article>
        <article><span>Alumnos creados</span><strong>{{ result.alumnos.created }}</strong></article>
        <article><span>Alumnos actualizados</span><strong>{{ result.alumnos.updated }}</strong></article>
        <article><span>Conceptos creados</span><strong>{{ result.conceptos?.created || 0 }}</strong></article>
        <article><span>Conceptos actualizados</span><strong>{{ result.conceptos?.updated || 0 }}</strong></article>
        <article><span>Saldos iniciales creados</span><strong>{{ result.saldos_iniciales?.created || 0 }}</strong></article>
        <article><span>Saldos ya existentes</span><strong>{{ result.saldos_iniciales?.updated || 0 }}</strong></article>
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
import { confirmImportacion } from '@/lib/swal'

const branches = ref([])
const selectedBranch = ref('POS')
const defaultCareer = ref('')
const selectedFile = ref(null)
const loading = ref(false)
const error = ref('')
const preview = ref(null)
const result = ref(null)

const selectedFileName = computed(() => selectedFile.value?.name || '')
const hasPreviewErrors = computed(() => Number(preview.value?.total_errores || 0) > 0)

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
  preview.value = null
  result.value = null
}

async function reviewImport() {
  if (!selectedFile.value) return
  loading.value = true
  error.value = ''
  result.value = null
  try {
    preview.value = await uploadFile('/importaciones/workbook/preview/', selectedFile.value, {
      sucursal: selectedBranch.value,
      carrera: defaultCareer.value,
    })
  } catch (err) {
    error.value = err.message || 'No se pudo revisar el archivo.'
  } finally {
    loading.value = false
  }
}

async function confirmImport() {
  if (!selectedFile.value || !preview.value || hasPreviewErrors.value) return
  const branch = branches.value.find((item) => item.codigo === selectedBranch.value)
  const confirmation = await confirmImportacion({
    archivo: preview.value.archivo,
    nuevos: preview.value.alumnos?.created || 0,
    actualizados: preview.value.alumnos?.updated || 0,
    conceptos: (preview.value.conceptos?.created || 0) + (preview.value.conceptos?.updated || 0),
    saldos: preview.value.saldos_iniciales?.created || 0,
    advertencias: preview.value.total_advertencias || 0,
    sucursal: branch ? `${branch.nombre} (${branch.codigo})` : selectedBranch.value,
  })
  if (!confirmation.isConfirmed) return

  loading.value = true
  error.value = ''
  try {
    result.value = await uploadFile('/importaciones/workbook/', selectedFile.value, {
      sucursal: selectedBranch.value,
      carrera: defaultCareer.value,
      preview_token: preview.value.preview_token,
    })
    preview.value = null
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
.imports-header, .imports-card, .imports-result { border: 1px solid var(--border); border-radius: 1rem; background: var(--surface); padding: 1.5rem; }
.imports-header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.imports-header h1, .imports-card h2, .imports-result h2 { margin: .2rem 0 .45rem; }
.imports-header p, .imports-card p { margin: 0; color: var(--text-secondary); }
.imports-header-icon, .imports-success-icon { width: 2.5rem; height: 2.5rem; color: var(--primary); flex: 0 0 auto; }
.imports-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-top: 1.25rem; }
.imports-fields label, .imports-file-field { display: grid; gap: .45rem; font-weight: 600; }
.imports-fields span, .imports-file-field span { color: var(--text-primary); }
.imports-fields small { font-weight: 400; color: var(--text-secondary); }
.imports-fields input, .imports-fields select { border: 1px solid var(--border); border-radius: .65rem; padding: .7rem .8rem; background: var(--surface); color: var(--text-primary); }
.imports-file-field { margin-top: 1rem; }
.imports-file-field small, .imports-hint { color: var(--text-secondary); font-weight: 400; }
.imports-file-picker { display: flex; align-items: center; gap: .75rem; min-width: 0; }
.imports-file-button { display: inline-flex !important; align-items: center; justify-content: center; flex: 0 0 auto; border: 1px solid var(--primary); border-radius: .65rem; padding: .7rem .9rem; color: var(--primary) !important; background: var(--surface); cursor: pointer; }
.imports-file-button input { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap; }
.imports-file-button:focus-within { outline: 3px solid color-mix(in srgb, var(--primary) 25%, transparent); outline-offset: 2px; }
.imports-file-name { min-width: 0; overflow: hidden; color: var(--text-secondary) !important; font-weight: 400; text-overflow: ellipsis; white-space: nowrap; }
.imports-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: .65rem; margin-top: 1.25rem; }
.imports-actions button { border: 0; border-radius: .65rem; padding: .7rem 1rem; cursor: pointer; font-weight: 700; }
.primary-button { background: var(--primary); color: var(--on-primary); }
.secondary-button { background: var(--surface-soft); color: var(--text-primary); }
.imports-actions button:disabled { cursor: not-allowed; opacity: .55; }
.imports-hint { margin-top: 1rem !important; font-size: .9rem; }
.imports-result-error { display: grid; gap: .35rem; color: var(--danger); background: var(--danger-soft); }
.imports-result-heading { display: flex; justify-content: space-between; gap: 1rem; }
.imports-summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .75rem; margin-top: 1.25rem; }
.imports-summary-grid article { display: grid; gap: .35rem; border-radius: .75rem; padding: .9rem; background: var(--surface-soft); }
.imports-summary-grid span { color: var(--text-secondary); font-size: .85rem; }
.imports-summary-grid strong { font-size: 1.45rem; }
.imports-summary-danger { color: var(--danger); background: var(--danger-soft) !important; }
.imports-preview-block { margin-top: 1.25rem; }
.imports-preview-error { display: grid; gap: .45rem; border: 1px solid color-mix(in srgb, var(--danger) 35%, var(--border)); border-radius: .75rem; padding: 1rem; color: var(--danger); background: var(--danger-soft); }
.imports-preview-error ul { margin: 0; padding-left: 1.2rem; }
.imports-preview-actions { display: flex; align-items: center; justify-content: flex-end; gap: 1rem; margin-top: 1.25rem; }
.imports-preview-status { color: var(--danger); font-weight: 600; }
.imports-warnings { margin-top: 1.25rem; border-top: 1px solid var(--border); padding-top: 1rem; }
.imports-warnings h3 { margin: 0 0 .5rem; }
.imports-warnings ul { display: grid; gap: .35rem; margin: 0; padding-left: 1.2rem; color: var(--warning); }
@media (max-width: 720px) {
  .imports-screen { padding: 1rem; }
  .imports-fields, .imports-summary-grid { grid-template-columns: 1fr; }
  .imports-actions { justify-content: stretch; }
  .imports-actions button { width: 100%; }
  .imports-file-picker { align-items: stretch; flex-direction: column; }
  .imports-file-button { width: 100%; }
}
</style>
