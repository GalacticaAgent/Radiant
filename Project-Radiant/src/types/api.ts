/**
 * API 请求和响应的类型定义
 */

/**
 * 通用API响应结构
 */
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

/**
 * 用户注册请求
 */
export interface SignupRequest {
  email: string;
  password: string;
  name?: string;
}

/**
 * 用户注册响应
 */
export interface SignupResponse {
  data: {
    id: string;
    email: string;
    user_metadata?: {
      name?: string;
    };
  };
  message: string;
}

/**
 * 认证检查响应
 */
export interface AuthCheckResponse {
  authenticated: boolean;
  user?: {
    id: string;
    email: string;
    user_metadata?: {
      name?: string;
    };
  };
  error?: string;
}

/**
 * 用户配置
 */
export interface UserProfile {
  name?: string;
  [key: string]: any;
}

/**
 * 用户配置响应
 */
export interface UserProfileResponse {
  user: {
    id: string;
    email: string;
    name: string;
    profile: UserProfile;
  };
}

/**
 * 审稿请求
 */
export interface ReviewRequest {
  content: string;
  reviewType?: 'comprehensive' | 'quick' | 'detailed';
}

/**
 * 审稿评分
 */
export interface ReviewScore {
  originality: number;
  methodology: number;
  clarity: number;
  significance: number;
  overall: number;
}

/**
 * 审稿结果
 */
export interface ReviewResult {
  reviewType: string;
  timestamp: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  score: ReviewScore;
  id?: string;
  contentPreview?: string;
}

/**
 * 审稿响应
 */
export interface ReviewResponse {
  review: ReviewResult;
}

/**
 * 审稿历史响应
 */
export interface ReviewHistoryResponse {
  history: ReviewResult[];
}

/**
 * 健康检查响应
 */
export interface HealthCheckResponse {
  status: string;
  timestamp: string;
}

/**
 * API错误类型
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
