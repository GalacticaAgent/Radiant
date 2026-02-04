# 前端开发需求文档

## 技术栈

### 核心框架
- **React 18** + **TypeScript**
- **Vite** (构建工具)
- **React Router v6** (路由管理)

### UI 组件库
- **Ant Design 5.x** 或 **Material-UI (MUI)**
- **Tailwind CSS** (样式工具)

### 状态管理
- **Zustand** 或 **Redux Toolkit**
- **React Query** (服务端状态管理)

### 图可视化
- **Cytoscape.js** 或 **D3.js** (知识图谱可视化)
- **React Flow** (备选方案)

### 其他工具
- **Axios** (HTTP 客户端)
- **React Markdown** (Markdown 渲染)
- **react-syntax-highlighter** (代码高亮)
- **ESLint + Prettier** (代码规范)

---

## 项目结构

```
frontend/
├── public/                  # 静态资源
├── src/
│   ├── api/                # API 请求封装
│   │   ├── auth.ts
│   │   ├── graph.ts
│   │   ├── chat.ts
│   │   ├── paper.ts
│   │   └── index.ts
│   ├── components/         # 通用组件
│   │   ├── Layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   ├── GraphViewer/    # 知识图谱可视化组件
│   │   │   ├── GraphCanvas.tsx
│   │   │   ├── NodeDetail.tsx
│   │   │   ├── GraphControls.tsx
│   │   │   └── GraphFilter.tsx
│   │   ├── Chat/           # 对话组件
│   │   │   ├── ChatBox.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageItem.tsx
│   │   │   └── InputArea.tsx
│   │   ├── Paper/          # 论文相关组件
│   │   │   ├── PaperUpload.tsx
│   │   │   ├── PaperViewer.tsx
│   │   │   ├── ReviewPanel.tsx
│   │   │   └── VersionHistory.tsx
│   │   └── Common/         # 通用组件
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorBoundary.tsx
│   │       └── MarkdownRenderer.tsx
│   ├── pages/              # 页面组件
│   │   ├── Login/
│   │   │   └── index.tsx
│   │   ├── Register/
│   │   │   └── index.tsx
│   │   ├── Home/
│   │   │   └── index.tsx
│   │   ├── Research/       # 调研功能
│   │   │   └── index.tsx
│   │   ├── IdeaValidation/ # Idea 检验
│   │   │   └── index.tsx
│   │   ├── PaperPolish/    # 论文打磨
│   │   │   └── index.tsx
│   │   ├── KnowledgeGraph/ # 知识图谱管理
│   │   │   └── index.tsx
│   │   └── Settings/
│   │       └── index.tsx
│   ├── hooks/              # 自定义 Hooks
│   │   ├── useAuth.ts
│   │   ├── useGraph.ts
│   │   ├── useChat.ts
│   │   └── usePaper.ts
│   ├── store/              # 状态管理
│   │   ├── authStore.ts
│   │   ├── graphStore.ts
│   │   ├── chatStore.ts
│   │   └── index.ts
│   ├── types/              # TypeScript 类型定义
│   │   ├── graph.ts
│   │   ├── chat.ts
│   │   ├── paper.ts
│   │   └── user.ts
│   ├── utils/              # 工具函数
│   │   ├── request.ts
│   │   ├── storage.ts
│   │   ├── format.ts
│   │   └── validator.ts
│   ├── styles/             # 全局样式
│   │   ├── global.css
│   │   └── variables.css
│   ├── App.tsx             # 根组件
│   ├── main.tsx            # 入口文件
│   └── router.tsx          # 路由配置
├── .env.development        # 开发环境变量
├── .env.production         # 生产环境变量
├── .eslintrc.js            # ESLint 配置
├── .prettierrc             # Prettier 配置
├── tsconfig.json           # TypeScript 配置
├── vite.config.ts          # Vite 配置
├── package.json
└── FRONTEND_REQUIREMENTS.md # 本文件
```

---

## 功能模块详细需求

### 1. 用户认证模块

#### 1.1 登录页面 (`/login`)
**功能**：
- 用户名/邮箱 + 密码登录
- 记住我选项
- 忘记密码链接
- 跳转注册链接

**组件**：
- `LoginForm` 组件
- 表单验证（邮箱格式、密码长度）
- 错误提示

**API 接口**：
- `POST /api/auth/login`

#### 1.2 注册页面 (`/register`)
**功能**：
- 用户名、邮箱、密码注册
- 密码强度提示
- 邮箱验证（可选）

**组件**：
- `RegisterForm` 组件
- 实时表单验证

**API 接口**：
- `POST /api/auth/register`

#### 1.3 个人设置页面 (`/settings`)
**功能**：
- 修改用户信息
- 修改密码
- API Key 管理（DeepSeek）
- 偏好设置（主题、语言等）

---

### 2. 知识图谱可视化模块

#### 2.1 图谱展示组件 (`GraphViewer`)
**功能**：
- 展示知识图谱（节点 + 边）
- 支持缩放、拖拽、平移
- 节点分类显示（文献、人事、代码）
- 节点颜色/大小映射（引用数、重要性）
- 边的类型显示（AUTHORED_BY, CITES 等）

**交互**：
- 点击节点显示详情
- 双击节点展开相关节点
- 右键菜单（隐藏、固定、导出）

**技术实现**：
- 使用 Cytoscape.js 或 D3.js
- 支持力导向布局
- 支持层次布局
- 性能优化：虚拟化渲染（大规模图谱）

**API 接口**：
- `GET /api/graph/subgraph?query=xxx`
- `GET /api/graph/node/:id`

#### 2.2 节点详情面板 (`NodeDetail`)
**功能**：
- 显示节点基本信息（标题、作者、时间等）
- 显示节点关系（相关论文、相关作者）
- 提供操作按钮（添加到私有图谱、导出）

#### 2.3 图谱筛选器 (`GraphFilter`)
**功能**：
- 按节点类型筛选
- 按时间范围筛选
- 按关键词筛选
- 按研究者筛选

#### 2.4 图谱控制面板 (`GraphControls`)
**功能**：
- 缩放控制
- 布局切换
- 全屏模式
- 导出图片/数据

---

### 3. 对话交互模块

#### 3.1 聊天界面 (`ChatBox`)
**功能**：
- 多轮对话展示
- 流式输出（打字机效果）
- 支持 Markdown 渲染
- 代码高亮
- 引用文献展示（可点击跳转）
- 历史对话记录

**组件**：
- `MessageList`：消息列表
- `MessageItem`：单条消息
  - 用户消息
  - AI 消息
  - 系统消息（爬取进度、任务状态）
- `InputArea`：输入框
  - 支持多行输入
  - 发送按钮
  - 文件上传按钮（上传论文）

**API 接口**：
- `POST /api/chat/send`（发送消息）
- `GET /api/chat/history`（获取历史）
- `WebSocket /ws/chat`（实时对话，可选）

**技术实现**：
- 使用 Server-Sent Events (SSE) 或 WebSocket 实现流式输出
- 使用 `react-markdown` 渲染 Markdown
- 使用 `react-syntax-highlighter` 渲染代码

---

### 4. 调研功能模块 (`/research`)

#### 4.1 研究方向检索
**功能**：
- 输入研究方向关键词
- 触发知识图谱爬取
- 显示爬取进度
- 展示相关文献列表
- 展示相关研究者
- 展示知识图谱

**交互流程**：
1. 用户输入"麦当劳"
2. 系统开始爬取（显示 Loading）
3. 实时更新爬取进度
4. 展示结果：
   - 文献列表（卡片式）
   - 研究者列表
   - 知识图谱可视化
   - AI 生成的总结

**API 接口**：
- `POST /api/research/start`（开始调研）
- `GET /api/research/status/:task_id`（查询进度）
- `GET /api/research/result/:task_id`（获取结果）

---

### 5. Idea 检验模块 (`/idea-validation`)

#### 5.1 Idea 输入界面
**功能**：
- 用户输入 Idea 描述
- 提交后触发检索和分析

#### 5.2 相关文献展示
**功能**：
- 展示与 Idea 相关的文献
- 高亮相似点
- 提供文献链接

#### 5.3 可行性评估
**功能**：
- AI 生成的可行性分析
- 列出支持/反对的理由
- 提供改进建议

**API 接口**：
- `POST /api/idea/validate`
- `GET /api/idea/related-papers`

---

### 6. 论文打磨模块 (`/paper-polish`)

#### 6.1 论文上传
**功能**：
- 支持 PDF 上传
- 支持 LaTeX 文件上传
- 文件预览

**组件**：
- `PaperUpload` 组件（拖拽上传）

**API 接口**：
- `POST /api/paper/upload`

#### 6.2 审稿人推荐
**功能**：
- 显示可能的审稿人列表
- 展示审稿人画像（研究方向、代表作）
- 用户可选择/调整审稿人

**API 接口**：
- `GET /api/paper/:id/reviewers`

#### 6.3 审稿意见展示
**功能**：
- 按审稿人分类显示意见
- 分类显示（优点、缺点、建议）
- 严重程度标记

**组件**：
- `ReviewPanel` 组件
  - 审稿人卡片
  - 意见列表
  - 严重程度标签

**API 接口**：
- `POST /api/paper/:id/review`（生成审稿意见）

#### 6.4 修改建议展示
**功能**：
- 基于审稿意见的修改建议
- 对比视图（原文 vs 修改建议）
- 支持接受/拒绝建议
- 生成新版本论文

**组件**：
- `SuggestionPanel` 组件
- `DiffViewer` 组件

**API 接口**：
- `POST /api/paper/:id/suggestions`（生成修改建议）
- `POST /api/paper/:id/apply-suggestion`（应用建议）

#### 6.5 版本历史
**功能**：
- 显示论文的所有版本
- 版本对比
- 回退到历史版本

**组件**：
- `VersionHistory` 组件

**API 接口**：
- `GET /api/paper/:id/versions`

---

### 7. 私有知识图谱管理 (`/knowledge-graph`)

#### 7.1 私有图谱创建
**功能**：
- 创建新的私有图谱
- 设置图谱名称和描述

#### 7.2 节点管理
**功能**：
- 手动添加节点（文献、人事、代码）
- 编辑节点信息
- 删除节点

#### 7.3 关系管理
**功能**：
- 添加节点间的关系
- 编辑关系类型
- 删除关系

#### 7.4 图谱可视化
**功能**：
- 展示私有图谱
- 与公有图谱合并展示

**API 接口**：
- `POST /api/private-graph/create`
- `POST /api/private-graph/:id/node`
- `POST /api/private-graph/:id/edge`
- `GET /api/private-graph/:id`

---

## 状态管理设计

### Auth Store
```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  register: (data: RegisterData) => Promise<void>;
}
```

### Graph Store
```typescript
interface GraphState {
  nodes: Node[];
  edges: Edge[];
  selectedNode: Node | null;
  filters: GraphFilters;
  layout: LayoutType;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  selectNode: (node: Node) => void;
  applyFilters: (filters: GraphFilters) => void;
}
```

### Chat Store
```typescript
interface ChatState {
  messages: Message[];
  isLoading: boolean;
  currentSessionId: string | null;
  sendMessage: (content: string) => Promise<void>;
  loadHistory: () => Promise<void>;
}
```

---

## API 请求封装

### 统一请求配置 (`utils/request.ts`)
```typescript
import axios from 'axios';

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
});

// 请求拦截器（添加 Token）
request.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器（统一错误处理）
request.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // Token 过期，跳转登录
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default request;
```

---

## 类型定义 (`types/`)

### Graph Types (`types/graph.ts`)
```typescript
export enum NodeType {
  PAPER = 'PAPER',
  PERSON = 'PERSON',
  ORGANIZATION = 'ORGANIZATION',
  CODE = 'CODE',
}

export interface Node {
  id: string;
  type: NodeType;
  label: string;
  properties: Record<string, any>;
}

export interface Edge {
  id: string;
  source: string;
  target: string;
  type: string;
  properties?: Record<string, any>;
}

export interface GraphData {
  nodes: Node[];
  edges: Edge[];
}
```

### Chat Types (`types/chat.ts`)
```typescript
export enum MessageRole {
  USER = 'USER',
  ASSISTANT = 'ASSISTANT',
  SYSTEM = 'SYSTEM',
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  references?: Reference[];
}

export interface Reference {
  type: 'paper' | 'person' | 'code';
  id: string;
  title: string;
  url?: string;
}
```

---

## 性能优化

### 1. 代码分割
- 使用 React.lazy 和 Suspense 懒加载页面
- 路由级别的代码分割

### 2. 图谱渲染优化
- 虚拟化渲染（大规模图谱）
- 节点聚合（超过 500 个节点时）
- Canvas 渲染替代 SVG（性能更好）

### 3. 请求优化
- 使用 React Query 缓存数据
- 防抖输入框搜索
- 图片懒加载

### 4. 构建优化
- Vite 生产构建优化
- 代码压缩和混淆
- Tree shaking

---

## 响应式设计

- 支持桌面端（≥1280px）
- 支持平板端（768px - 1279px）
- 支持移动端（<768px）
- 图谱可视化在移动端提供简化版本

---

## 测试

### 单元测试
- 使用 Vitest + React Testing Library
- 覆盖核心组件和工具函数

### E2E 测试
- 使用 Playwright
- 覆盖关键用户流程

---

## 部署

### 构建命令
```bash
npm run build
```

### 部署方式
- 静态部署（Nginx）
- CDN 加速
- 环境变量配置

---

## 开发规范

### 命名规范
- 组件：PascalCase (`GraphViewer.tsx`)
- 函数/变量：camelCase (`getUserInfo`)
- 常量：UPPER_SNAKE_CASE (`API_BASE_URL`)
- CSS 类名：kebab-case (`graph-viewer`)

### 组件规范
- 优先使用函数组件 + Hooks
- 组件文件和样式文件同目录
- 复杂组件拆分子组件

### 提交规范
- feat: 新功能
- fix: 修复
- refactor: 重构
- docs: 文档更新
- style: 样式调整
- test: 测试相关

---

## 待开发功能清单

### Phase 1（基础功能）
- [ ] 登录/注册页面
- [ ] 主界面布局
- [ ] 知识图谱可视化组件
- [ ] 对话界面
- [ ] API 接口封装

### Phase 2（核心功能）
- [ ] 调研功能页面
- [ ] Idea 检验页面
- [ ] 论文上传功能
- [ ] 审稿意见展示

### Phase 3（高级功能）
- [ ] 私有知识图谱管理
- [ ] 版本历史对比
- [ ] 多模型选择
- [ ] 协作功能

### Phase 4（优化）
- [ ] 性能优化
- [ ] 移动端适配
- [ ] 国际化
- [ ] 暗色主题
