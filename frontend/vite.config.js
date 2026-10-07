import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // El watcher nativo de Vite revienta con `UNKNOWN: unknown error, watch`
    // cuando el proyecto vive en una unidad de red (O:\ es un share mapeado).
    // Con VITE_FORCE_POLLING=1 se usa polling: más lento, pero estable.
    watch: process.env.VITE_FORCE_POLLING ? { usePolling: true, interval: 1000 } : undefined,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    // Mismo proxy que en desarrollo, para probar el build de producción con
    // `vite preview` sin tocar la configuración de la API.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
