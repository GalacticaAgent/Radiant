# 项目配置说明

本文档说明如何配置项目的前后端环境。

## 环境变量配置

### 前端环境变量

创建 `.env` 文件（参考 `env.example`）：

```env
# Supabase 配置
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# API 配置
VITE_API_BASE_URL=https://your-project.supabase.co/functions/v1
VITE_API_FUNCTION_NAME=make-server-df059afa

# 应用配置
VITE_APP_NAME=Radiant
VITE_APP_VERSION=1.0.0
```

### 后端环境变量

后端环境变量需要在 Supabase 控制台中配置：

1. 登录 [Supabase Dashboard](https://app.supabase.com)
2. 选择你的项目
3. 进入 **Settings** > **Edge Functions** > **Secrets**
4. 添加以下环境变量：
   - `SUPABASE_URL`: 你的 Supabase 项目 URL
   - `SUPABASE_SERVICE_ROLE_KEY`: 你的服务角色密钥（在 Settings > API 中获取）

## API 配置

### API 路由

所有 API 路由定义在 `src/config/api.ts` 中：

- **认证相关**:
  - `POST /signup` - 用户注册
  - `GET /auth-check` - 检查认证状态

- **用户相关**:
  - `GET /user-profile` - 获取用户配置
  - `POST /user-profile` - 更新用户配置

- **审稿相关**:
  - `POST /review` - 提交审稿
  - `GET /review-history` - 获取审稿历史

- **系统相关**:
  - `GET /health` - 健康检查

### 使用 API 客户端

项目提供了统一的 API 客户端，位于 `src/utils/api/client.ts`：

```typescript
import { apiClient } from '@/utils/api/client';

// GET 请求
const data = await apiClient.get('/endpoint', { token: 'your-token' });

// POST 请求
const result = await apiClient.post('/endpoint', { data }, { token: 'your-token' });
```

### 使用 API 服务

推荐使用封装好的服务函数（位于 `src/utils/api/services.ts`）：

```typescript
import { authService, userService, reviewService } from '@/utils/api/services';

// 用户注册
await authService.signup({ email, password, name }, anonKey);

// 获取用户配置
const profile = await userService.getProfile(token);

// 提交审稿
const review = await reviewService.submitReview(token, { content, reviewType });
```

## 后端配置

### Deno 配置

后端使用 Deno 运行时，配置文件位于 `supabase/functions/server/deno.json`。

### 部署

使用 Supabase CLI 部署 Edge Functions：

```bash
# 安装 Supabase CLI
npm install -g supabase

# 登录
supabase login

# 链接项目
supabase link --project-ref your-project-ref

# 部署函数
supabase functions deploy server
```

## 类型定义

所有 API 类型定义位于 `src/types/api.ts`，包括：

- `ApiResponse<T>` - 通用 API 响应
- `SignupRequest` / `SignupResponse` - 注册请求/响应
- `AuthCheckResponse` - 认证检查响应
- `UserProfile` / `UserProfileResponse` - 用户配置
- `ReviewRequest` / `ReviewResponse` - 审稿请求/响应
- `ApiError` - API 错误类

## 错误处理

### 前端错误处理

API 客户端会自动处理错误并抛出 `ApiError`：

```typescript
import { ApiError } from '@/utils/api/client';

try {
  await userService.getProfile(token);
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API错误:', error.status, error.message);
  }
}
```

### 后端错误处理

后端使用统一的错误处理中间件，所有错误都会被标准化处理：

- `400` - 客户端错误（参数错误、验证失败等）
- `401` - 未授权
- `500` - 服务器内部错误

## 日志

### 后端日志

后端使用自定义日志工具（`supabase/functions/server/utils/logger.ts`）：

```typescript
import { logger } from './utils/logger.ts';

logger.info('操作成功');
logger.error('操作失败', error);
```

日志级别：
- `DEBUG` - 调试信息
- `INFO` - 一般信息
- `WARN` - 警告
- `ERROR` - 错误

## 开发建议

1. **使用环境变量**: 不要在代码中硬编码配置值
2. **使用类型定义**: 充分利用 TypeScript 类型系统
3. **统一错误处理**: 使用提供的错误处理机制
4. **API 服务封装**: 使用封装好的服务函数而不是直接调用 API 客户端
5. **日志记录**: 在后端适当位置添加日志记录

## 故障排查

### 前端问题

1. **API 请求失败**: 检查环境变量是否正确配置
2. **认证失败**: 检查 token 是否有效
3. **CORS 错误**: 检查后端 CORS 配置

### 后端问题

1. **函数部署失败**: 检查 `deno.json` 配置
2. **环境变量未找到**: 在 Supabase 控制台检查环境变量配置
3. **数据库连接失败**: 检查 `SUPABASE_URL` 和 `SUPABASE_SERVICE_ROLE_KEY`
