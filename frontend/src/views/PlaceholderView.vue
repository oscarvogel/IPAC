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
  background: #ffffff;
  border: 1px dashed #c9c9d4;
  border-radius: 12px;
  text-align: center;
  color: #2a2a35;
}

.placeholder-view h1 {
  margin: 0 0 0.75rem;
  font-size: 1.75rem;
}

.placeholder-view p {
  margin: 0;
  color: #6a6a78;
  line-height: 1.5;
}
</style>
