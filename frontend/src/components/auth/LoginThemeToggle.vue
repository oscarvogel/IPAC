<template>
  <button
    type="button"
    class="login-theme-toggle"
    :aria-label="themeLabel"
    :title="themeLabel"
    @click="toggleTheme"
  >
    <SunIcon v-if="isDark" aria-hidden="true" />
    <MoonIcon v-else aria-hidden="true" />
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { MoonIcon, SunIcon } from '@heroicons/vue/24/outline'
import { useTheme } from '@/composables/useTheme'

const { isDark, toggleTheme } = useTheme()
const themeLabel = computed(() => isDark.value ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro')
</script>
