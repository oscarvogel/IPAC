<template>
  <div ref="appShell" class="app-shell" :class="{ 'sidebar-is-open': sidebarOpen }">
    <a class="skip-link" href="#main-content">Ir al contenido principal</a>
    <AppSidebar ref="sidebarComponent" :open="sidebarOpen" @close="closeSidebar" />
    <button
      ref="sidebarBackdrop"
      class="sidebar-backdrop"
      type="button"
      aria-label="Cerrar navegación"
      :aria-hidden="sidebarOpen ? undefined : 'true'"
      :tabindex="sidebarOpen ? 0 : -1"
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
import { animateSidebar } from '@/lib/motion'

const route = useRoute()
const sidebarOpen = ref(false)
const mainContent = ref(null)
const appShell = ref(null)
const sidebarComponent = ref(null)
const sidebarBackdrop = ref(null)
const mobileMediaQuery = window.matchMedia?.('(max-width: 760px)')
let sidebarTween = null
let sidebarAnimationId = 0

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

watch(sidebarOpen, async (open) => {
  syncBodyScrollLock()
  const animationId = ++sidebarAnimationId
  await nextTick()
  if (animationId !== sidebarAnimationId) return

  const shell = appShell.value
  const sidebar = sidebarComponent.value?.$el
  const backdrop = sidebarBackdrop.value
  if (!mobileMediaQuery?.matches || !sidebar) return

  sidebarTween?.kill()
  shell?.classList.add('sidebar-gsap-active')
  sidebarTween = animateSidebar(sidebar, backdrop, open, () => {
    if (animationId === sidebarAnimationId) shell?.classList.remove('sidebar-gsap-active')
  })
})

onMounted(() => {
  mobileMediaQuery?.addEventListener?.('change', syncBodyScrollLock)
  syncBodyScrollLock()
})

onBeforeUnmount(() => {
  sidebarTween?.kill()
  appShell.value?.classList.remove('sidebar-gsap-active')
  mobileMediaQuery?.removeEventListener?.('change', syncBodyScrollLock)
  document.body.classList.remove('sidebar-scroll-locked')
})
</script>
