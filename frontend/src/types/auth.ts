export interface User {
  id: string
  email: string
  username: string
  full_name?: string
  avatar_url?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
  full_name?: string
}

export interface RegisterResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface RefreshTokenRequest {
  refresh_token?: string
}

export interface RefreshTokenResponse {
  access_token: string
  token_type: string
}

export interface LogoutRequest {
  token?: string
}

export interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}
