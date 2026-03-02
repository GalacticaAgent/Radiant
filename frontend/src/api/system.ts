import axios from 'axios'
import { authStore } from '../store/authStore'

export interface ApiResponse<T> {
  code: number
  msg: string
  data: T
}

export type SystemHealth = {
  status: string
  celery_run_inline: boolean
  broker_ok: boolean
  backend_ok: boolean
  worker_ok?: boolean | null
  workers?: number | null
  errors?: string[]
}

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || '').replace(/\/api\/v1\/?$/, ''),
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = authStore.getState().token
  if (token) {
    config.headers = config.headers || {}
    ;(config.headers as any).Authorization = `Bearer ${token}`
  }
  return config
})

export const systemAPI = {
  health: (options?: { signal?: AbortSignal }) =>
    api.get<ApiResponse<SystemHealth>>('/api/system/health', { signal: options?.signal }).then((r) => r.data.data),
}

