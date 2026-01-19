/**
 * 统一的API客户端封装
 */
import { buildApiUrl, API_CONFIG } from '@/config/api';
import type { ApiResponse } from '@/types/api';
import { ApiError } from '@/types/api';

/**
 * 请求选项
 */
export interface RequestOptions extends RequestInit {
  token?: string;
  timeout?: number;
}

/**
 * API客户端类
 */
class ApiClient {
  private defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  /**
   * 发送HTTP请求
   */
  private async request<T = any>(
    url: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const {
      token,
      timeout = API_CONFIG.timeout,
      headers = {},
      ...fetchOptions
    } = options;

    // 构建请求头
    const requestHeaders: HeadersInit = {
      ...this.defaultHeaders,
      ...headers,
    };

    // 添加认证token
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }

    // 创建AbortController用于超时控制
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers: requestHeaders,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // 解析响应
      const data: ApiResponse<T> = await response.json();

      // 检查响应状态
      if (!response.ok) {
        throw new ApiError(
          response.status,
          data.error || data.message || '请求失败',
          data
        );
      }

      // 返回数据
      return (data.data ?? data) as T;
    } catch (error: any) {
      clearTimeout(timeoutId);

      // 处理AbortError（超时）
      if (error.name === 'AbortError') {
        throw new ApiError(408, '请求超时，请稍后重试');
      }

      // 处理网络错误
      if (error instanceof TypeError) {
        throw new ApiError(0, '网络错误，请检查网络连接');
      }

      // 如果是ApiError，直接抛出
      if (error instanceof ApiError) {
        throw error;
      }

      // 其他错误
      throw new ApiError(500, error.message || '未知错误');
    }
  }

  /**
   * GET 请求
   */
  async get<T = any>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    return this.request<T>(buildApiUrl(endpoint), {
      ...options,
      method: 'GET',
    });
  }

  /**
   * POST 请求
   */
  async post<T = any>(
    endpoint: string,
    body?: any,
    options: RequestOptions = {}
  ): Promise<T> {
    return this.request<T>(buildApiUrl(endpoint), {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * PUT 请求
   */
  async put<T = any>(
    endpoint: string,
    body?: any,
    options: RequestOptions = {}
  ): Promise<T> {
    return this.request<T>(buildApiUrl(endpoint), {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * DELETE 请求
   */
  async delete<T = any>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    return this.request<T>(buildApiUrl(endpoint), {
      ...options,
      method: 'DELETE',
    });
  }

  /**
   * PATCH 请求
   */
  async patch<T = any>(
    endpoint: string,
    body?: any,
    options: RequestOptions = {}
  ): Promise<T> {
    return this.request<T>(buildApiUrl(endpoint), {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    });
  }
}

// 导出单例实例
export const apiClient = new ApiClient();

// 导出ApiError类
export { ApiError } from '@/types/api';
