// Composable que permite a una vista inyectar acciones en el topbar
// (boton "Nuevo alumno", "Nueva caja", etc).
//
// Patron: la vista llama setTopbarActions([...]) en onMounted y
// setTopbarActions([]) en onBeforeUnmount. AppTopbar lee de useTopbarActions.

import { ref, readonly } from 'vue'

const actions = ref([])

export function setTopbarActions(newActions) {
  actions.value = newActions || []
}

export function useTopbarActions() {
  return {
    actions: readonly(actions),
    setTopbarActions,
  }
}
