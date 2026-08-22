import { beforeEach, describe, expect, it } from 'vitest'
import { useTheme } from './useTheme'

describe('tema de interfaz', () => {
  beforeEach(() => localStorage.clear())

  it('alterna el tema, lo aplica al documento y persiste la preferencia', () => {
    const { theme, toggleTheme } = useTheme()
    const initial = theme.value

    toggleTheme()

    expect(theme.value).not.toBe(initial)
    expect(document.documentElement.dataset.theme).toBe(theme.value)
    expect(document.documentElement.style.colorScheme).toBe(theme.value)
    expect(localStorage.getItem('ipac-theme')).toBe(theme.value)
  })
})
