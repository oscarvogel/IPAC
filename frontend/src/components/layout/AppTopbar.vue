<template>
  <header class="topbar text-text-primary">
    <button
      class="mobile-menu-button"
      type="button"
      aria-label="Abrir navegación"
      @click="$emit('toggle-sidebar')"
    >
      <Bars3Icon aria-hidden="true" />
    </button>

    <Transition name="topbar-heading" mode="out-in">
      <div :key="route.path" class="topbar-heading">
        <p class="eyebrow">Panel de trabajo</p>
        <h1>{{ title }}</h1>
      </div>
    </Transition>

    <div v-if="isDashboard" class="dashboard-context-actions">
      <button
        class="icon-button"
        type="button"
        :aria-label="`Período actual: ${periodLabel}`"
      >
        <CalendarDaysIcon aria-hidden="true" />
      </button>

      <label class="branch-select">
        <span class="sr-only">Sucursal</span>
        <select v-model="selectedSucursalId" aria-label="Sucursal">
          <option
            v-for="sucursal in sucursales"
            :key="sucursal.id"
            :value="String(sucursal.id)"
          >
            {{ sucursal.nombre }}
          </option>
        </select>
        <ChevronDownIcon aria-hidden="true" />
      </label>
    </div>

    <div v-else-if="actions.length" class="top-actions">
      <button
        v-for="action in actions"
        :key="action.label"
        :class="action.variant === 'primary' ? 'new-button' : 'secondary-button'"
        type="button"
        :disabled="action.disabled"
        @click="action.onClick"
      >
        {{ action.label }}
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Bars3Icon, CalendarDaysIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'
import { useAuth } from '@/composables/useAuth'
import { useCatalogos } from '@/composables/useCatalogos'
import { useDashboardFilters } from '@/composables/useDashboardFilters'
import { useTopbarActions } from '@/composables/useTopbarActions'

defineEmits(['toggle-sidebar'])

const route = useRoute()
const { user } = useAuth()
const { sucursales, loadCatalogos } = useCatalogos()
const { selectedSucursalId } = useDashboardFilters()
const { actions: providedActions } = useTopbarActions()

const titles = {
  '/dashboard': 'Dashboard',
  '/alumnos': 'Alumnos',
  '/deudores': 'Deudores',
  '/caja': 'Caja',
  '/conceptos': 'Conceptos',
  '/reportes': 'Reportes',
  '/sucursales': 'Sucursales',
  '/usuarios': 'Usuarios',
}

const title = computed(() => titles[route.path] || 'IPAC')
const actions = computed(() => providedActions.value || [])
const isDashboard = computed(() => route.path === '/dashboard')
const periodLabel = new Intl.DateTimeFormat('es-AR', {
  month: 'long',
  year: 'numeric',
}).format(new Date())

onMounted(() => {
  loadCatalogos()
})

watch(
  [sucursales, user],
  () => {
    if (selectedSucursalId.value || !sucursales.value.length) return
    const preferred = user.value?.perfil?.sucursal?.id
    const available = sucursales.value.find((sucursal) => sucursal.id === preferred)
    selectedSucursalId.value = String(available?.id || sucursales.value[0].id)
  },
  { immediate: true },
)
</script>
