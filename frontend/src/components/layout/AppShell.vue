<template>
  <div class="app-shell" :class="{ 'sidebar-is-open': sidebarOpen }">
    <a class="skip-link" href="#main-content">Ir al contenido principal</a>
    <AppSidebar :open="sidebarOpen" @close="closeSidebar" />
    <button
      v-if="sidebarOpen"
      class="sidebar-backdrop"
      type="button"
      aria-label="Cerrar navegación"
      @click="sidebarOpen = false"
    />
    <section class="workspace" :inert="sidebarOpen ? '' : undefined">
      <AppTopbar :sidebar-open="sidebarOpen" @toggle-sidebar="toggleSidebar" />
      <main id="main-content" ref="mainContent" class="workspace-content" tabindex="-1">
        <RouterView v-slot="{ Component, route: currentRoute }">
          <Transition name="route-view" mode="out-in">
            <Suspense timeout="0">
              <template #default>
                <component :is="Component" :key="currentRoute.name || currentRoute.path" />
              </template>
              <template #fallback>
                <AppPageState loading label="la vista seleccionada" />
              </template>
            </Suspense>
          </Transition>
        </RouterView>
      </main>
    </section>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterView } from 'vue-router'
import { useRoute } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'
import AppPageState from '@/components/ui/AppPageState.vue'

const route = useRoute()
const sidebarOpen = ref(false)
const mainContent = ref(null)
const mobileMediaQuery = window.matchMedia?.('(max-width: 760px)')

function syncBodyScrollLock() {
  const isMobile = mobileMediaQuery?.matches ?? false
  document.body.classList.toggle('sidebar-scroll-locked', sidebarOpen.value && isMobile)
}

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebar() {
  sidebarOpen.value = false
}

watch(
  () => route.path,
  async () => {
    sidebarOpen.value = false
    await nextTick()
    mainContent.value?.focus({ preventScroll: true })
  },
)

watch(sidebarOpen, syncBodyScrollLock)

onMounted(() => {
  mobileMediaQuery?.addEventListener?.('change', syncBodyScrollLock)
  syncBodyScrollLock()
})

onBeforeUnmount(() => {
  mobileMediaQuery?.removeEventListener?.('change', syncBodyScrollLock)
  document.body.classList.remove('sidebar-scroll-locked')
})
</script>
