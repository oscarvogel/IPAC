<template>
  <div class="app-shell" :class="{ 'sidebar-is-open': sidebarOpen }">
    <AppSidebar @close="sidebarOpen = false" />
    <button
      v-if="sidebarOpen"
      class="sidebar-backdrop"
      type="button"
      aria-label="Cerrar navegación"
      @click="sidebarOpen = false"
    />
    <section class="workspace">
      <AppTopbar @toggle-sidebar="sidebarOpen = !sidebarOpen" />
      <main class="workspace-content">
        <RouterView v-slot="{ Component, route: currentRoute }">
          <Transition name="route-view" mode="out-in">
            <component :is="Component" :key="currentRoute.name || currentRoute.path" />
          </Transition>
        </RouterView>
      </main>
    </section>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { RouterView } from 'vue-router'
import { useRoute } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'

const route = useRoute()
const sidebarOpen = ref(false)

watch(
  () => route.path,
  () => {
    sidebarOpen.value = false
  },
)
</script>
