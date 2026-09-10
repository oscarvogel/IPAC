// Catalogos compartidos: sucursales, carreras, conceptos cobrables.
// Estado singleton a nivel de modulo. Cualquier vista que los necesite
// llama a loadCatalogos() la primera vez; despues quedan en memoria.

import { ref, readonly } from 'vue'
import { apiRequest } from '@/lib/api'

const sucursales = ref([])
const carreras = ref([])
const conceptos = ref([])
const tiposDescuento = ref([])
const reglasRecargo = ref([])
const loaded = ref(false)
const loading = ref(false)
let loadingPromise = null
let activeLoads = 0
const resourcePromises = new Map()
const resourceLoaded = new Set()

const catalogResources = {
  sucursales: {
    path: '/sucursales/',
    assign: (data) => { sucursales.value = data.results || [] },
  },
  carreras: {
    path: '/carreras/',
    assign: (data) => { carreras.value = data.results || [] },
  },
  conceptos: {
    path: '/conceptos/',
    assign: (data) => { conceptos.value = data.results || [] },
  },
  tiposDescuento: {
    path: '/tipos-descuento/',
    assign: (data) => { tiposDescuento.value = data.results || [] },
  },
  reglasRecargo: {
    path: '/reglas-recargo/',
    assign: (data) => { reglasRecargo.value = data.results || [] },
  },
}

function setLoading(delta) {
  activeLoads += delta
  loading.value = activeLoads > 0
}

function loadCatalogo(resourceName, force = false) {
  const resource = catalogResources[resourceName]
  if (!resource) return Promise.reject(new Error(`Catálogo desconocido: ${resourceName}`))
  if (resourceLoaded.has(resourceName) && !force) return Promise.resolve()
  if (resourcePromises.has(resourceName)) return resourcePromises.get(resourceName)

  setLoading(1)
  const promise = apiRequest(resource.path)
    .then((data) => {
      resource.assign(data)
      resourceLoaded.add(resourceName)
    })
    .finally(() => {
      resourcePromises.delete(resourceName)
      setLoading(-1)
    })

  resourcePromises.set(resourceName, promise)
  return promise
}

function loadCatalogos(force = false) {
  if (loaded.value && !force) return
  if (loadingPromise) return loadingPromise

  loadingPromise = Promise.all(Object.keys(catalogResources).map((resourceName) => (
    loadCatalogo(resourceName, force)
  )))
    .then(() => {
      loaded.value = true
    })
    .finally(() => {
      loadingPromise = null
    })

  return loadingPromise
}

export function useCatalogos() {
  return {
    sucursales: readonly(sucursales),
    carreras: readonly(carreras),
    conceptos: readonly(conceptos),
    tiposDescuento: readonly(tiposDescuento),
    reglasRecargo: readonly(reglasRecargo),
    loaded: readonly(loaded),
    loading: readonly(loading),
    loadCatalogo,
    loadCatalogos,
  }
}
