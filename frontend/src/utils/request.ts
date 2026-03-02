import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { authStore } from '../store/authStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

interface ApiError {
  message: string
  code?: string
  status?: number
  details?: Record<string, string>
}

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = authStore.getState().token
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

        // Handle 401 Unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const { refreshToken } = authStore.getState()
            if (!refreshToken) {
              throw new Error('No refresh token found')
            }

            // Attempt to refresh token
            const response = await axios.post(
              `${API_BASE_URL}/auth/refresh`,
              { refresh_token: refreshToken },
              {
                headers: {
                  'Content-Type': 'application/json',
                },
              }
            )

            const newToken = response.data.access_token
            authStore.getState().setToken(newToken)

            // Retry original request with new token
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
            }
            return this.client(originalRequest)
          } catch (refreshError) {
            // Token refresh failed, logout user
            authStore.getState().logout()
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(this.transformError(error))
      }
    )
  }

  private transformError(error: AxiosError): ApiError {
    const apiError: ApiError = {
      message: 'An unexpected error occurred',
      status: error.response?.status,
    }

    if ((error as any).code) {
      apiError.code = String((error as any).code)
    }

    const message = (error.message || '').toLowerCase()
    if ((error as any).name === 'CanceledError' || apiError.code === 'ERR_CANCELED' || message.includes('canceled')) {
      apiError.message = 'Request canceled'
      apiError.code = 'ERR_CANCELED'
      return apiError
    }
    if (message.includes('err_aborted') || message.includes('aborted')) {
      apiError.message = 'Request aborted'
      apiError.code = apiError.code || 'ERR_ABORTED'
      return apiError
    }

    if (error.response?.data) {
      const data = error.response.data as Record<string, unknown>
      
      // Handle various error message formats
      let errorMessage = data.message || data.detail
      
      if (errorMessage) {
        if (typeof errorMessage === 'string') {
          apiError.message = errorMessage
        } else if (Array.isArray(errorMessage)) {
          // Handle FastAPI validation errors (array of objects)
          apiError.message = errorMessage
            .map((item: any) => item.msg || JSON.stringify(item))
            .join('; ')
        } else if (typeof errorMessage === 'object') {
          // Handle object error
          apiError.message = (errorMessage as any).msg || JSON.stringify(errorMessage)
        } else {
          apiError.message = String(errorMessage)
        }
      }

      apiError.code = data.code as string
      apiError.details = data.details as Record<string, string>
    } else if (error.message) {
      apiError.message = error.message
    }

    return apiError
  }

  public getInstance(): AxiosInstance {
    return this.client
  }
}

export const apiClient = new ApiClient()
export default apiClient.getInstance()
