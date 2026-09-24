<template>
  <section class="unresolved">
    <div v-if="loading" class="empty">Cargando consultas…</div>
    <div v-else-if="!items.length" class="empty">No hay consultas para estos filtros.</div>

    <article v-for="item in items" :key="item.id" class="unresolved-card">
      <header>
        <div>
          <span class="badge">{{ labels[item.categoria] || item.categoria }}</span>
          <strong>{{ item.pregunta }}</strong>
        </div>
        <span class="status">{{ item.estado }}</span>
      </header>
      <div class="meta">
        <span>{{ item.usuario }}</span>
        <span>{{ item.sucursal }}</span>
        <span>{{ formatDate(item.creado) }}</span>
      </div>
      <p v-if="item.respuesta" class="response">{{ item.respuesta }}</p>
      <footer v-if="item.estado === 'pendiente'">
        <button
          :data-testid="`create-article-${item.id}`"
          type="button"
          class="btn-primary"
          @click="$emit('create-article', item)"
        >
          Crear artículo
        </button>
        <button type="button" class="btn-secondary" @click="$emit('resolve', item)">Marcar resuelta</button>
        <button type="button" class="btn-secondary" @click="$emit('ignore', item)">Ignorar</button>
      </footer>
      <p v-else-if="item.articulo_titulo" class="resolved-with">
        Resuelta con: {{ item.articulo_titulo }}
      </p>
    </article>
  </section>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})
defineEmits(['create-article', 'resolve', 'ignore'])

const labels = {
  no_documentada: 'No documentada',
  sin_datos: 'Sin datos',
  sin_permiso: 'Sin permiso',
  fuera_de_alcance: 'Fuera de alcance',
  error_ia: 'Error IA',
  error_herramienta: 'Error de herramienta',
}

function formatDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('es-AR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value))
}
</script>

<style scoped>
.unresolved { display: grid; gap: .8rem; }
.unresolved-card { display: grid; gap: .65rem; border: 1px solid var(--color-border); border-radius: .9rem; padding: .9rem; background: var(--color-surface); }
.unresolved-card header { display: flex; justify-content: space-between; gap: .75rem; }
.unresolved-card header > div { display: grid; gap: .35rem; }
.badge { width: fit-content; border-radius: 999px; padding: .2rem .5rem; background: var(--primary-soft); color: var(--primary); font-size: .7rem; font-weight: 800; }
.status { color: var(--color-text-secondary); font-size: .78rem; text-transform: capitalize; }
.meta { display: flex; flex-wrap: wrap; gap: .75rem; color: var(--color-text-secondary); font-size: .78rem; }
.response { margin: 0; color: var(--color-text-secondary); }
.unresolved-card footer { display: flex; flex-wrap: wrap; gap: .5rem; }
.btn-primary, .btn-secondary { border-radius: .65rem; padding: .5rem .7rem; cursor: pointer; }
.btn-primary { border: 0; background: var(--primary); color: white; font-weight: 700; }
.btn-secondary { border: 1px solid var(--color-border); background: var(--color-surface); color: var(--color-text-primary); }
.resolved-with { margin: 0; font-size: .8rem; color: var(--color-text-secondary); }
.empty { padding: 2rem; text-align: center; color: var(--color-text-secondary); }
</style>
