<template><section class="news-index"><header><h2>Cambios de esta versión</h2><p>Novedades de IPAC, con su fecha y las pantallas donde podés encontrarlas.</p></header><article v-for="item in novedades" :key="item.titulo"><time :datetime="item.fecha">{{ formatDate(item.fecha) }}</time><h3>{{ item.titulo }}</h3><p>{{ item.descripcion }}</p><nav aria-label="Pantallas relacionadas"><RouterLink v-for="link in item.enlaces" :key="link.ruta" :to="link.ruta">{{ link.texto }}</RouterLink></nav></article></section></template>
<script setup>
import { novedades } from '@/content/guias'
import { formatDate } from '@/lib/formatters'
</script>
<style scoped>
.news-index{max-width:900px;display:grid;gap:1rem;color:var(--text-primary)}.news-index article{padding:1.25rem;border:1px solid var(--border);border-radius:.9rem;background:var(--surface)}.news-index h2{font-size:1.15rem}.news-index time,.news-index p{color:var(--text-secondary)}.news-index nav{display:flex;flex-wrap:wrap;gap:.8rem}.news-index a{display:inline-flex;align-items:center;min-height:44px;color:var(--primary);font-weight:700}
</style>
