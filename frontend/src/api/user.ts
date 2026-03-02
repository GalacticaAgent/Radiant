import axiosInstance from './index'

export interface UserProfile {
  id: string
  username: string
  email: string
  is_active: boolean
  created_at: string
  updated_at?: string | null
  deepseek_api_key?: string | null
  preferences?: Record<string, unknown> | null
}

export const userAPI = {
  getProfile: () => axiosInstance.get<UserProfile>('/user/profile').then((r) => r.data),
  updateProfile: (payload: Partial<Pick<UserProfile, 'username' | 'email' | 'deepseek_api_key' | 'preferences'>>) =>
    axiosInstance.put<UserProfile>('/user/profile', payload).then((r) => r.data),
}

