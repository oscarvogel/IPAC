<template>
  <section class="placeholder-view">
    <h1>{{ title }}</h1>
    <p v-if="note">{{ note }}</p>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  note: { type: String, default: '' },
})
</script>

<style scoped>
.placeholder-view {
  max-width: 720px;
  margin: 4rem auto;
  padding: 2.5rem;
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: 12px;
  text-align: center;
  color: var(--text-primary);
}

.placeholder-view h1 {
  margin: 0 0 0.75rem;
  font-size: 1.75rem;
}

.placeholder-view p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.5;
}
</style>
