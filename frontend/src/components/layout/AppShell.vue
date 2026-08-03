<template>
  <div class="app-shell" :class="{ 'sidebar-is-open': sidebarOpen }">
    <a class="skip-link" href="#main-content">Ir al contenido principal</a>
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
      <main id="main-content" ref="mainContent" class="workspace-content" tabindex="-1">
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
import { nextTick, ref, watch } from 'vue'
import { RouterView } from 'vue-router'
import { useRoute } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'

const route = useRoute()
const sidebarOpen = ref(false)
const mainContent = ref(null)

watch(
  () => route.path,
  async () => {
    sidebarOpen.value = false
    await nextTick()
    mainContent.value?.focus({ preventScroll: true })
  },
)
</script>
