import { Hono } from 'npm:hono';
import { cors } from 'npm:hono/cors';
import { logger as honoLogger } from 'npm:hono/logger';
import * as kv from './kv_store.tsx';
import { verifyAuth, getSupabaseClient } from './utils/auth.ts';
import { handleError, createErrorResponse, AppError } from './utils/errors.ts';
import { logger } from './utils/logger.ts';

const app = new Hono();

// Middleware
app.use('*', cors({
  origin: '*',
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
}));
app.use('*', honoLogger());

const supabase = getSupabaseClient();

// 全局错误处理
app.onError((err, c) => {
  logger.error('请求处理错误:', err);
  const errorResponse = handleError(err);
  return c.json(errorResponse, errorResponse.statusCode || 500);
});

// 用户注册路由
app.post('/make-server-df059afa/signup', async (c) => {
  try {
    const { email, password, name } = await c.req.json();

    if (!email || !password) {
      throw new AppError(400, '邮箱和密码不能为空', 'ERR_MISSING_FIELDS');
    }

    // 验证邮箱格式
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      throw new AppError(400, '邮箱格式不正确', 'ERR_INVALID_EMAIL');
    }

    // 验证密码长度
    if (password.length < 6) {
      throw new AppError(400, '密码长度至少为6位', 'ERR_PASSWORD_TOO_SHORT');
    }

    const { data, error } = await supabase.auth.admin.createUser({
      email,
      password,
      user_metadata: { name: name || '' },
      email_confirm: true,
    });

    if (error) {
      logger.error('注册用户失败:', error);
      throw new AppError(400, error.message, 'ERR_USER_CREATION_FAILED');
    }

    logger.info(`用户注册成功: ${email}`);
    return c.json({ data, message: '注册成功' });
  } catch (error) {
    if (error instanceof AppError) {
      throw error;
    }
    logger.error('注册用户时发生错误:', error);
    throw new AppError(500, '服务器错误', 'ERR_INTERNAL');
  }
});

// 检查认证状态
app.get('/make-server-df059afa/auth-check', async (c) => {
  try {
    const authHeader = c.req.header('Authorization');
    const user = await verifyAuth(authHeader);
    logger.debug(`认证检查成功: ${user.email}`);
    return c.json({ authenticated: true, user });
  } catch (error) {
    if (error instanceof AppError && error.statusCode === 401) {
      return c.json({ authenticated: false }, 401);
    }
    throw error;
  }
});

// 获取用户配置
app.get('/make-server-df059afa/user-profile', async (c) => {
  try {
    const user = await verifyAuth(c.req.header('Authorization'));
    
    // 从KV存储获取用户配置
    const profile = await kv.get(`user_profile_${user.id}`);

    logger.debug(`获取用户配置: ${user.id}`);
    return c.json({
      user: {
        id: user.id,
        email: user.email,
        name: user.user_metadata?.name || '',
        profile: profile || {},
      },
    });
  } catch (error) {
    if (error instanceof AppError && error.statusCode === 401) {
      return c.json(createErrorResponse(401, '未授权', 'ERR_UNAUTHORIZED'), 401);
    }
    throw error;
  }
});

// 更新用户配置
app.post('/make-server-df059afa/user-profile', async (c) => {
  try {
    const user = await verifyAuth(c.req.header('Authorization'));
    const profileData = await c.req.json();

    if (!profileData || typeof profileData !== 'object') {
      throw new AppError(400, '配置数据格式错误', 'ERR_INVALID_DATA');
    }

    // 保存用户配置到KV存储
    await kv.set(`user_profile_${user.id}`, profileData);

    logger.info(`更新用户配置: ${user.id}`);
    return c.json({ message: '配置更新成功', profile: profileData });
  } catch (error) {
    if (error instanceof AppError && error.statusCode === 401) {
      return c.json(createErrorResponse(401, '未授权', 'ERR_UNAUTHORIZED'), 401);
    }
    throw error;
  }
});

// 模拟审稿路由
app.post('/make-server-df059afa/review', async (c) => {
  try {
    const user = await verifyAuth(c.req.header('Authorization'));
    const { content, reviewType } = await c.req.json();

    if (!content || typeof content !== 'string' || content.trim().length === 0) {
      throw new AppError(400, '内容不能为空', 'ERR_EMPTY_CONTENT');
    }

    if (content.length > 100000) {
      throw new AppError(400, '内容过长，请限制在100000字符以内', 'ERR_CONTENT_TOO_LONG');
    }

    // 模拟审稿结果（实际应用中这里会调用AI服务）
    const mockReview = {
      reviewType: reviewType || 'comprehensive',
      timestamp: new Date().toISOString(),
      summary: '这是一个初步的审稿意见...',
      strengths: [
        '研究问题明确，具有一定的学术价值',
        '方法论较为完善',
        '数据分析较为全面',
      ],
      weaknesses: [
        '文献综述部分可以更加深入',
        '部分实验设计可以更加严谨',
        '结论部分需要进一步强化',
      ],
      suggestions: [
        '建议补充最新的相关文献',
        '建议增加对照实验验证假设',
        '建议在讨论部分增加对研究局限性的分析',
      ],
      score: {
        originality: 7,
        methodology: 8,
        clarity: 7,
        significance: 7,
        overall: 7.25,
      },
    };

    // 保存审稿历史
    const reviewHistory = (await kv.get(`review_history_${user.id}`)) || [];
    reviewHistory.unshift({
      id: crypto.randomUUID(),
      ...mockReview,
      contentPreview: content.substring(0, 100),
    });

    // 只保留最近20条记录
    if (reviewHistory.length > 20) {
      reviewHistory.splice(20);
    }

    await kv.set(`review_history_${user.id}`, reviewHistory);

    logger.info(`审稿完成: ${user.id}, 类型: ${reviewType || 'comprehensive'}`);
    return c.json({ review: mockReview });
  } catch (error) {
    if (error instanceof AppError && error.statusCode === 401) {
      return c.json(createErrorResponse(401, '未授权', 'ERR_UNAUTHORIZED'), 401);
    }
    throw error;
  }
});

// 获取审稿历史
app.get('/make-server-df059afa/review-history', async (c) => {
  try {
    const user = await verifyAuth(c.req.header('Authorization'));
    const reviewHistory = (await kv.get(`review_history_${user.id}`)) || [];

    logger.debug(`获取审稿历史: ${user.id}, 记录数: ${reviewHistory.length}`);
    return c.json({ history: reviewHistory });
  } catch (error) {
    if (error instanceof AppError && error.statusCode === 401) {
      return c.json(createErrorResponse(401, '未授权', 'ERR_UNAUTHORIZED'), 401);
    }
    throw error;
  }
});

// 健康检查
app.get('/make-server-df059afa/health', (c) => {
  logger.debug('健康检查请求');
  return c.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

Deno.serve(app.fetch);
