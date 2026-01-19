/**
 * API服务封装 - 业务逻辑层
 */
import { apiClient } from './client';
import { API_ENDPOINTS } from '@/config/api';
import type {
  SignupRequest,
  SignupResponse,
  AuthCheckResponse,
  UserProfile,
  UserProfileResponse,
  ReviewRequest,
  ReviewResponse,
  ReviewHistoryResponse,
  HealthCheckResponse,
} from '@/types/api';

/**
 * 认证服务
 */
export const authService = {
  /**
   * 用户注册
   */
  async signup(data: SignupRequest, anonKey: string): Promise<SignupResponse> {
    return apiClient.post<SignupResponse>(
      API_ENDPOINTS.AUTH.SIGNUP,
      data,
      {
        headers: {
          Authorization: `Bearer ${anonKey}`,
        },
      }
    );
  },

  /**
   * 检查认证状态
   */
  async checkAuth(token: string): Promise<AuthCheckResponse> {
    return apiClient.get<AuthCheckResponse>(API_ENDPOINTS.AUTH.AUTH_CHECK, {
      token,
    });
  },
};

/**
 * 用户服务
 */
export const userService = {
  /**
   * 获取用户配置
   */
  async getProfile(token: string): Promise<UserProfileResponse> {
    return apiClient.get<UserProfileResponse>(API_ENDPOINTS.USER.PROFILE, {
      token,
    });
  },

  /**
   * 更新用户配置
   */
  async updateProfile(
    token: string,
    profile: UserProfile
  ): Promise<{ message: string; profile: UserProfile }> {
    return apiClient.post(
      API_ENDPOINTS.USER.PROFILE,
      profile,
      {
        token,
      }
    );
  },
};

/**
 * 审稿服务
 */
export const reviewService = {
  /**
   * 提交审稿
   */
  async submitReview(
    token: string,
    data: ReviewRequest
  ): Promise<ReviewResponse> {
    return apiClient.post<ReviewResponse>(
      API_ENDPOINTS.REVIEW.SUBMIT,
      data,
      {
        token,
      }
    );
  },

  /**
   * 获取审稿历史
   */
  async getHistory(token: string): Promise<ReviewHistoryResponse> {
    return apiClient.get<ReviewHistoryResponse>(
      API_ENDPOINTS.REVIEW.HISTORY,
      {
        token,
      }
    );
  },
};

/**
 * 系统服务
 */
export const systemService = {
  /**
   * 健康检查
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    return apiClient.get<HealthCheckResponse>(API_ENDPOINTS.SYSTEM.HEALTH);
  },
};
