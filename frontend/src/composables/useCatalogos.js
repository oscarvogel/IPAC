// Catalogos compartidos: sucursales, carreras, conceptos cobrables.
// Estado singleton a nivel de modulo. Cualquier vista que los necesite
// llama a loadCatalogos() la primera vez; despues quedan en memoria.

import { ref, readonly } from 'vue'
import { apiRequest } from '@/lib/api'

const sucursales = ref([])
const carreras = ref([])
const conceptos = ref([])
const loaded = ref(false)
const loading = ref(false)

async function loadCatalogos(force = false) {
  if (loaded.value && !force) return
  loading.value = true
  try {
    const [suc, car, con] = await Promise.all([
      apiRequest('/sucursales/'),
      apiRequest('/carreras/'),
      apiRequest('/conceptos/'),
    ])
    sucursales.value = suc.results || []
    carreras.value = car.results || []
    conceptos.value = con.results || []
    loaded.value = true
  } finally {
    loading.value = false
  }
}

export function useCatalogos() {
  return {
    sucursales: readonly(sucursales),
    carreras: readonly(carreras),
    conceptos: readonly(conceptos),
    loaded: readonly(loaded),
    loading: readonly(loading),
    loadCatalogos,
  }
}
