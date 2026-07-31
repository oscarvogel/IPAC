import { ref } from 'vue'

const selectedSucursalId = ref('')

export function useDashboardFilters() {
  return {
    selectedSucursalId,
  }
}
