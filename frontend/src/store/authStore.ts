import { create } from 'zustand'
import { User, AuthState } from '../types/auth'

interface AuthStoreState extends AuthState {
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  setRefreshToken: (token: string | null) => void
  setIsLoading: (isLoading: boolean) => void
  setError: (error: string | null) => void
  setAuthenticated: (isAuthenticated: boolean) => void
  logout: () => void
  hydrate: () => void
  clearError: () => void
}

const STORAGE_KEY = 'radiant_auth_token'
const REFRESH_TOKEN_KEY = 'radiant_refresh_token'
const USER_STORAGE_KEY = 'radiant_user'

export const authStore = create<AuthStoreState>((set) => {
  // Load from localStorage on initialization
  const savedToken = localStorage.getItem(STORAGE_KEY)
  const savedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
  const savedUser = localStorage.getItem(USER_STORAGE_KEY)

  const initialState: AuthState = {
    user: savedUser ? JSON.parse(savedUser) : null,
    token: savedToken,
    refreshToken: savedRefreshToken,
    isAuthenticated: !!savedToken,
    isLoading: false,
    error: null,
  }

  return {
    ...initialState,

    setUser: (user) =>
      set(() => {
        if (user) {
          localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
        } else {
          localStorage.removeItem(USER_STORAGE_KEY)
        }
        return { user, isAuthenticated: !!localStorage.getItem(STORAGE_KEY) && !!user }
      }),

    setToken: (token) =>
      set(() => {
        if (token) {
          localStorage.setItem(STORAGE_KEY, token)
        } else {
          localStorage.removeItem(STORAGE_KEY)
        }
        return { token, isAuthenticated: !!token }
      }),

    setRefreshToken: (token) =>
      set(() => {
        if (token) {
          localStorage.setItem(REFRESH_TOKEN_KEY, token)
        } else {
          localStorage.removeItem(REFRESH_TOKEN_KEY)
        }
        return { refreshToken: token }
      }),

    setIsLoading: (isLoading) => set({ isLoading }),

    setError: (error) => set({ error }),

    setAuthenticated: (isAuthenticated) => set({ isAuthenticated }),

    logout: () =>
      set({
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        error: null,
      }),

    hydrate: () => {
      const savedToken = localStorage.getItem(STORAGE_KEY)
      const savedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      const savedUser = localStorage.getItem(USER_STORAGE_KEY)

      set({
        token: savedToken,
        refreshToken: savedRefreshToken,
        user: savedUser ? JSON.parse(savedUser) : null,
        isAuthenticated: !!savedToken,
      })
    },

    clearError: () => set({ error: null }),
  }
})
