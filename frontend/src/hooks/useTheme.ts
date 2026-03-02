import { useEffect } from 'react'
import { uiStore } from '../store/uiStore'

export const useTheme = () => {
  const theme = uiStore((state) => state.theme)
  const setTheme = uiStore((state) => state.setTheme)
  const toggleTheme = uiStore((state) => state.toggleTheme)

  useEffect(() => {
    // Hydrate theme from localStorage on mount
    uiStore.getState().hydrate()
  }, [])

  return {
    theme,
    setTheme,
    toggleTheme,
    isDark: theme === 'dark',
  }
}
