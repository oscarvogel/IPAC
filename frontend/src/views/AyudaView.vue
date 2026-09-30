<template>
  <section class="help-index"><header><h2>Ayuda para operar IPAC</h2><p>Elegí una guía para ver pasos, ejemplos y términos.</p></header>
    <article v-for="guia in disponibles" :key="guia.id"><AyudaContextual :guia="guia.id" /><RouterLink :to="guia.ruta">Abrir {{ { pagos: 'Alumnos', cierre: 'Caja', reportes: 'Reportes' }[guia.id] }}</RouterLink></article>
    <p>Las acciones disponibles dependen de tu perfil y de tus sucursales autorizadas.</p>
  </section>
</template>
<script setup>
import { computed } from 'vue'
import { guias } from '@/content/guias'
import { useAuth } from '@/composables/useAuth'
import AyudaContextual from '@/components/ui/AyudaContextual.vue'
const auth = useAuth()
const disponibles = computed(() => guias.filter(guia => !guia.permiso || auth.can(guia.permiso)))
</script>
<style scoped>
.help-index{max-width:900px;display:grid;gap:1rem;color:var(--text-primary)}.help-index article{padding:1rem;border:1px solid var(--border);border-radius:.9rem;background:var(--surface)}.help-index a{display:inline-flex;align-items:center;min-height:44px;color:var(--primary);font-weight:700}.help-index p{color:var(--text-secondary)}
</style>
