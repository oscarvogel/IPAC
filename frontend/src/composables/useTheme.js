import { computed, ref } from 'vue'

const STORAGE_KEY = 'ipac-theme'
const saved = typeof localStorage !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null
const preferredDark = typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: dark)').matches
const theme = ref(saved === 'dark' || saved === 'light' ? saved : (preferredDark ? 'dark' : 'light'))

function applyTheme() {
  document.documentElement.dataset.theme = theme.value
  document.documentElement.style.colorScheme = theme.value
}

if (typeof document !== 'undefined') applyTheme()

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem(STORAGE_KEY, theme.value)
  applyTheme()
}

export function useTheme() {
  return {
    theme: computed(() => theme.value),
    isDark: computed(() => theme.value === 'dark'),
    toggleTheme,
  }
}
