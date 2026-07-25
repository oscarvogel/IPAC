// Config de Vitest. Usa jsdom para poder testear composables y componentes Vue
// que dependen de localStorage / fetch. Reusa el alias `@/` del vite.config.js.

import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.test.js'],
  },
})
