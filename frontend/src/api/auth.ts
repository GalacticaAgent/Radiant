import axiosInstance from './index'
import { LoginRequest, LoginResponse, RegisterRequest, RegisterResponse } from '../types/auth'

export const authAPI = {
  login: (data: LoginRequest): Promise<LoginResponse> =>
    axiosInstance.post('/auth/login', {
      username_or_email: data.email,
      password: data.password
    }).then((res) => res.data),

  register: (data: RegisterRequest): Promise<RegisterResponse> =>
    axiosInstance.post('/auth/register', data).then((res) => res.data),

  logout: (): Promise<void> =>
    axiosInstance.post('/auth/logout').then((res) => res.data),

  refresh: (): Promise<{ access_token: string; token_type: string }> =>
    axiosInstance.post('/auth/refresh', {}).then((res) => res.data),

  getCurrentUser: () =>
    axiosInstance.get('/auth/me').then((res) => res.data),
}
