<template>
  <div class="app-shell">
    <AppSidebar />
    <section class="workspace">
      <AppTopbar />
      <RouterView />
    </section>
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'
</script>
