/**
 * 认证工具函数
 */
import { createClient } from 'npm:@supabase/supabase-js';
import { AppError } from './errors.ts';

const supabase = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
);

/**
 * 从请求头中提取并验证token
 */
export async function verifyAuth(authHeader: string | undefined) {
  if (!authHeader) {
    throw new AppError(401, '未授权：缺少认证token', 'ERR_NO_TOKEN');
  }

  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') {
    throw new AppError(401, '未授权：token格式错误', 'ERR_INVALID_TOKEN_FORMAT');
  }

  const token = parts[1];
  const { data: { user }, error } = await supabase.auth.getUser(token);

  if (error || !user) {
    throw new AppError(401, '未授权：token无效或已过期', 'ERR_INVALID_TOKEN');
  }

  return user;
}

/**
 * 获取Supabase客户端
 */
export function getSupabaseClient() {
  return supabase;
}
