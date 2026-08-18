import { readonly, ref } from 'vue'
import { apiRequest } from '@/lib/api'

const deudores = ref([])
const pagination = ref({ count: 0, page: 1, pageSize: 10, next: null, previous: null })
const loading = ref(false)
const error = ref('')

async function loadDeudores(query = {}) {
  loading.value = true
  error.value = ''
  try {
    const data = await apiRequest('/deudores/', { query })
    deudores.value = data.results || []
    pagination.value = {
      count: Number(data.count || 0),
      page: Number(data.page || query.page || 1),
      pageSize: Number(data.page_size || query.page_size || 10),
      next: data.next || null,
      previous: data.previous || null,
    }
    return data
  } catch (err) {
    error.value = err.message || 'No se pudo cargar la cartera de deudores.'
    throw err
  } finally {
    loading.value = false
  }
}

export function useDeudores() {
  return {
    deudores: readonly(deudores),
    pagination: readonly(pagination),
    loading: readonly(loading),
    error: readonly(error),
    loadDeudores,
  }
}
