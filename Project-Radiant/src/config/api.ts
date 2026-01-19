/**
 * API 配置和路由常量
 */

// 从环境变量获取配置，如果没有则使用默认值
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://nccpnvlhzymsxuhoarrf.supabase.co/functions/v1',
  functionName: import.meta.env.VITE_API_FUNCTION_NAME || 'make-server-df059afa',
  timeout: 30000, // 30秒超时
} as const;

/**
 * API 路由端点
 */
export const API_ENDPOINTS = {
  // 认证相关
  AUTH: {
    SIGNUP: '/signup',
    AUTH_CHECK: '/auth-check',
  },
  // 用户相关
  USER: {
    PROFILE: '/user-profile',
  },
  // 审稿相关
  REVIEW: {
    SUBMIT: '/review',
    HISTORY: '/review-history',
  },
  // 系统相关
  SYSTEM: {
    HEALTH: '/health',
  },
} as const;

/**
 * 构建完整的API URL
 */
export function buildApiUrl(endpoint: string): string {
  return `${API_CONFIG.baseURL}/${API_CONFIG.functionName}${endpoint}`;
}

/**
 * 获取所有API端点URL
 */
export const API_URLS = {
  auth: {
    signup: buildApiUrl(API_ENDPOINTS.AUTH.SIGNUP),
    authCheck: buildApiUrl(API_ENDPOINTS.AUTH.AUTH_CHECK),
  },
  user: {
    profile: buildApiUrl(API_ENDPOINTS.USER.PROFILE),
  },
  review: {
    submit: buildApiUrl(API_ENDPOINTS.REVIEW.SUBMIT),
    history: buildApiUrl(API_ENDPOINTS.REVIEW.HISTORY),
  },
  system: {
    health: buildApiUrl(API_ENDPOINTS.SYSTEM.HEALTH),
  },
} as const;
