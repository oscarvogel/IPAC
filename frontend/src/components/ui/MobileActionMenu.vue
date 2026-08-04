<template>
  <div ref="menuRoot" class="mobile-action-menu">
    <button
      type="button"
      class="mobile-action-trigger"
      :aria-label="label"
      :aria-expanded="open"
      @click="open = !open"
    >
      <EllipsisHorizontalIcon aria-hidden="true" />
    </button>

    <Transition name="mobile-menu">
      <div v-if="open" class="mobile-action-popover" role="menu" @click="closeAfterAction">
        <slot />
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { EllipsisHorizontalIcon } from '@heroicons/vue/24/outline'

const mountedMenus = new Set()

function handleGlobalPointerDown(event) {
  mountedMenus.forEach((menu) => {
    if (menu.open.value && !menu.root.value?.contains(event.target)) menu.open.value = false
  })
}

function handleGlobalKeydown(event) {
  if (event.key !== 'Escape') return
  mountedMenus.forEach((menu) => {
    menu.open.value = false
  })
}

defineProps({
  label: { type: String, default: 'Ver acciones' },
})

const menuRoot = ref(null)
const open = ref(false)
const menuInstance = { root: menuRoot, open }

function closeAfterAction(event) {
  if (event.target.closest('button')) open.value = false
}

onMounted(() => {
  if (!mountedMenus.size) {
    document.addEventListener('pointerdown', handleGlobalPointerDown)
    document.addEventListener('keydown', handleGlobalKeydown)
  }
  mountedMenus.add(menuInstance)
})

onBeforeUnmount(() => {
  mountedMenus.delete(menuInstance)
  if (!mountedMenus.size) {
    document.removeEventListener('pointerdown', handleGlobalPointerDown)
    document.removeEventListener('keydown', handleGlobalKeydown)
  }
})
</script>
