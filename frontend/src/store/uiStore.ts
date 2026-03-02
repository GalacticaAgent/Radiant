import { create } from 'zustand'

type Theme = 'light' | 'dark'

interface UIState {
  theme: Theme
  sidebarCollapsed: boolean
  currentPage: string
  isMobileMenuOpen: boolean
}

interface UIStoreState extends UIState {
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  toggleSidebar: () => void
  setCurrentPage: (page: string) => void
  setMobileMenuOpen: (open: boolean) => void
  hydrate: () => void
}

const THEME_STORAGE_KEY = 'radiant_theme'

// Get system preference for theme
const getSystemTheme = (): Theme => {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

// Get initial theme from localStorage or system preference
const getInitialTheme = (): Theme => {
  const saved = localStorage.getItem(THEME_STORAGE_KEY)
  if (saved === 'light' || saved === 'dark') {
    return saved
  }
  return getSystemTheme()
}

export const uiStore = create<UIStoreState>((set) => {
  const initialTheme = getInitialTheme()

  return {
    theme: initialTheme,
    sidebarCollapsed: false,
    currentPage: 'home',
    isMobileMenuOpen: false,

    setTheme: (theme) =>
      set(() => {
        localStorage.setItem(THEME_STORAGE_KEY, theme)
        // Update document attribute for CSS theme switching
        if (typeof document !== 'undefined') {
          if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark')
          } else {
            document.documentElement.removeAttribute('data-theme')
          }
        }
        return { theme }
      }),

    toggleTheme: () =>
      set((state) => {
        const newTheme: Theme = state.theme === 'light' ? 'dark' : 'light'
        localStorage.setItem(THEME_STORAGE_KEY, newTheme)
        if (typeof document !== 'undefined') {
          if (newTheme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark')
          } else {
            document.documentElement.removeAttribute('data-theme')
          }
        }
        return { theme: newTheme }
      }),

    setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

    toggleSidebar: () =>
      set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

    setCurrentPage: (page) => set({ currentPage: page }),

    setMobileMenuOpen: (open) => set({ isMobileMenuOpen: open }),

    hydrate: () => {
      const theme = getInitialTheme()
      if (typeof document !== 'undefined') {
        if (theme === 'dark') {
          document.documentElement.setAttribute('data-theme', 'dark')
        } else {
          document.documentElement.removeAttribute('data-theme')
        }
      }
      set({ theme })
    },
  }
})
