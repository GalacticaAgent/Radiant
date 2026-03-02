# Radiant 后端 - 快速启动指南

## 当前状态

✅ **阶段三核心模块已完成** - 后端核心功能开发

已完成的功能模块：
- ✅ 用户认证系统（注册、登录、JWT）
- ✅ DeepSeek API 集成
- ✅ 知识图谱服务（查询、子图提取）
- ✅ 对话服务（聊天、上下文管理）
- ✅ Celery 任务队列配置
- ✅ 数据库连接层（Neo4j, PostgreSQL, Redis）

---

## 环境要求

- Python 3.10+
- Docker Desktop（用于数据库）
- 所有数据库服务已启动（Neo4j, PostgreSQL, Redis）

### DOC 文件解析（可选）

项目在解析 `.doc` 文件时需要 `LibreOffice (soffice)` 用于将 DOC 转换为 DOCX。你可以选择：

- 系统安装 LibreOffice，并确保 `soffice` 在 PATH 中
- 或将 LibreOffice 解压到项目内并通过环境变量指定 `SOFFICE_PATH`
- 或使用 Docker Compose 运行后端（后端镜像会安装 LibreOffice，终端用户无需额外安装）

### 本地向量 Embedding（可选）

默认 Docker 镜像不会安装本地向量模型依赖（体积很大，会拉取 torch）。如需开启 `EMBEDDING_PROVIDER=local` / `sentence_transformers`：

- 本地开发：安装 `backend/requirements-embeddings-local.txt`
- Docker 构建：`docker build --build-arg WITH_LOCAL_EMBEDDINGS=true ...`

Windows 下可使用脚本将 LibreOffice MSI 下载并解压到 `backend/.tools/libreoffice`：

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File scripts\setup_libreoffice_windows.ps1
```

解压完成后，将输出的 `soffice.exe` 路径写入 `backend/.env` 的 `SOFFICE_PATH` 或在启动后端前设置：

```powershell
Set-Item -Path Env:SOFFICE_PATH -Value "C:\path\to\soffice.exe"
```

---

## 启动步骤

### 1. 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

后端的 `.env` 文件已自动配置，包含：
- 数据库连接信息
- DeepSeek API Key：在 `.env` 中配置（不要提交到仓库）
- JWT 密钥

### 3. 初始化数据库

```bash
cd backend
python -m app.db.init_db
```

这将：
- 创建 PostgreSQL 表结构
- 验证 Neo4j 连接
- 验证 Redis 连接

### 4. 启动后端服务

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动。

### 5. 访问 API 文档

打开浏览器访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## API 端点概览

### 认证相关

- **POST** `/api/v1/auth/register` - 用户注册
- **POST** `/api/v1/auth/login` - 用户登录
- **POST** `/api/v1/auth/refresh` - 刷新 Token
- **GET** `/api/v1/auth/me` - 获取当前用户信息
- **POST** `/api/v1/auth/logout` - 用户登出

### 知识图谱相关

- **GET** `/api/v1/graph/search` - 搜索节点
- **GET** `/api/v1/graph/subgraph` - 提取子图
- **GET** `/api/v1/graph/node/{node_id}` - 获取节点详情
- **GET** `/api/v1/graph/researcher/{researcher_id}/papers` - 获取研究者论文
- **GET** `/api/v1/graph/paper/{paper_id}/related` - 获取相关论文

### 对话相关

- **POST** `/api/v1/chat/send` - 发送消息
- **GET** `/api/v1/chat/history` - 获取对话历史
- **GET** `/api/v1/chat/stream` - 流式对话
- **POST** `/api/v1/chat/clear` - 清除会话

---

## 测试 API

### 1. 注册用户

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. 登录获取 Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "testuser",
    "password": "password123"
  }'
```

返回的 `access_token` 用于后续请求。

### 3. 搜索知识图谱

```bash
curl -X GET "http://localhost:8000/api/v1/graph/search?q=transformer" \
  -H "Authorization: Bearer {your_access_token}"
```

### 4. 发送聊天消息

```bash
curl -X POST "http://localhost:8000/api/v1/chat/send" \
  -H "Authorization: Bearer {your_access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "请介绍一下 Transformer 模型",
    "search_graph": true
  }'
```

---

## 项目结构

```
backend/
├── app/
│   ├── api/                # API 路由
│   │   ├── deps.py         # 依赖注入（JWT 验证）
│   │   └── v1/
│   │       ├── auth.py     # 认证 API
│   │       ├── graph.py    # 图谱 API
│   │       ├── chat.py     # 对话 API
│   │       └── ...
│   ├── core/               # 核心配置
│   │   ├── config.py       # 配置管理
│   │   ├── security.py     # JWT 和密码处理
│   │   └── celery_app.py   # Celery 配置
│   ├── db/                 # 数据库
│   │   ├── postgres.py     # PostgreSQL 连接
│   │   ├── neo4j.py        # Neo4j 连接
│   │   ├── redis.py        # Redis 连接
│   │   └── init_db.py      # 数据库初始化
│   ├── models/             # SQLAlchemy 模型
│   │   ├── user.py         # 用户模型
│   │   └── conversation.py # 对话模型
│   ├── schemas/            # Pydantic Schemas
│   │   ├── user.py         # 用户相关
│   │   └── chat.py         # 对话相关
│   ├── services/           # 业务逻辑
│   │   ├── auth_service.py      # 认证服务
│   │   ├── llm_service.py       # DeepSeek API 服务
│   │   ├── graph_service.py     # 图谱服务
│   │   └── chat_service.py      # 对话服务
│   └── main.py             # FastAPI 应用入口
├── .env                    # 环境变量
├── requirements.txt        # Python 依赖
└── README.md               # 本文件
```

---

## 数据库访问

### PostgreSQL
- 主机: localhost:5432
- 数据库: radiant
- 用户名: postgres
- 密码: （在本地 `.env` 中配置）

### Neo4j
- Web 界面: http://localhost:7474
- Bolt URI: bolt://localhost:7687
- 用户名: neo4j
- 密码: （在本地 `.env` 中配置）

### Redis
- URL: redis://localhost:6379/0

---

## 常见问题

### Q: 如何启动 Celery Worker？

```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

### Q: 如何查看 Celery 任务状态？

启动 Flower 监控：
```bash
celery -A app.core.celery_app flower
```

然后访问 http://localhost:5555

### Q: 数据库连接失败？

确认所有 Docker 容器正在运行：
```bash
docker ps
```

应该看到：
- radiant-neo4j
- radiant-postgres
- radiant-redis

### Q: DeepSeek API 调用失败？

检查环境变量中的 API Key 是否正确：
```bash
grep DEEPSEEK_API_KEY backend/.env
```

---

## 下一步开发

阶段三已完成核心后端功能。接下来可以：

1. **添加更多 API 功能**
   - 论文上传和分析
   - 审稿人推荐
   - Idea 可行性评估
   - 爬虫任务管理

2. **前端开发**（阶段四）
   - React 应用开发
   - 知识图谱可视化
   - 对话界面

3. **爬虫功能**
   - arXiv 爬虫
   - Semantic Scholar 爬虫
   - GitHub 爬虫

---

## 技术栈

- **框架**: FastAPI 0.104.1
- **数据库**:
  - PostgreSQL 16（用户数据）
  - Neo4j 5.14（知识图谱）
  - Redis 5.0（缓存、队列）
- **ORM**: SQLAlchemy 2.0
- **认证**: JWT (python-jose)
- **任务队列**: Celery 5.3
- **AI**: DeepSeek API (OpenAI SDK)

---

**祝开发顺利！🚀**
