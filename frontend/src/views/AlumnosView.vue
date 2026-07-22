<template>
  <div class="alumnos-screen">
    <p class="alumnos-skeleton">Cargando modulo de alumnos...</p>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import { useAlumnos } from '@/composables/useAlumnos'
import { useCatalogos } from '@/composables/useCatalogos'
import { usePagos } from '@/composables/usePagos'
import { useTopbarActions } from '@/composables/useTopbarActions'

const { loadAlumnos } = useAlumnos()
const { loadCatalogos } = useCatalogos()
const { loadPagos } = usePagos()
const { setTopbarActions } = useTopbarActions()

onMounted(async () => {
  await Promise.all([loadCatalogos(), loadAlumnos(), loadPagos()])
})

onBeforeUnmount(() => {
  setTopbarActions([])
})
</script>

<style scoped>
.alumnos-skeleton {
  padding: 2rem;
  text-align: center;
  color: var(--muted);
}
</style>
