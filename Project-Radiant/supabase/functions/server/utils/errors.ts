/**
 * 错误处理工具
 */

export class AppError extends Error {
  constructor(
    public statusCode: number,
    public message: string,
    public code?: string
  ) {
    super(message);
    this.name = 'AppError';
  }
}

/**
 * 创建标准错误响应
 */
export function createErrorResponse(
  statusCode: number,
  message: string,
  code?: string
) {
  return {
    error: message,
    code: code || `ERR_${statusCode}`,
    timestamp: new Date().toISOString(),
  };
}

/**
 * 错误处理中间件
 */
export function handleError(error: unknown) {
  if (error instanceof AppError) {
    return createErrorResponse(error.statusCode, error.message, error.code);
  }

  if (error instanceof Error) {
    console.error('未处理的错误:', error);
    return createErrorResponse(500, '服务器内部错误', 'ERR_INTERNAL');
  }

  return createErrorResponse(500, '未知错误', 'ERR_UNKNOWN');
}
