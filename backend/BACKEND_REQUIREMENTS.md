# 后端开发需求文档

## 技术栈

### 核心框架
- **Python 3.10+**
- **FastAPI** (Web 框架)
- **Uvicorn** (ASGI 服务器)
- **Pydantic** (数据验证)

### 数据库
- **Neo4j** (图数据库，存储知识图谱)
- **PostgreSQL** (关系数据库，存储用户、配置等)
- **SQLAlchemy** (ORM)
- **Alembic** (数据库迁移)

### 任务队列
- **Celery** (异步任务)
- **Redis** (消息队列 + 缓存)

### 爬虫
- **Scrapy** (爬虫框架)
- **BeautifulSoup4** (HTML 解析)
- **aiohttp** (异步 HTTP 请求)

### AI 集成
- **DeepSeek API** (主要 LLM)
- **LangChain** (Agent 编排)
- **OpenAI SDK** (兼容 DeepSeek API)

### 文件处理
- **PyPDF2 / pdfplumber** (PDF 解析)
- **python-docx** (Word 文档)

### 其他工具
- **python-jose** (JWT)
- **passlib** (密码哈希)
- **python-multipart** (文件上传)
- **pytest** (测试框架)

---

## 项目结构

```
backend/
├── app/
│   ├── api/                    # API 路由
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 认证相关
│   │   │   ├── graph.py        # 知识图谱相关
│   │   │   ├── chat.py         # 对话相关
│   │   │   ├── research.py     # 调研功能
│   │   │   ├── idea.py         # Idea 检验
│   │   │   ├── paper.py        # 论文打磨
│   │   │   ├── user.py         # 用户管理
│   │   │   └── private_graph.py # 私有图谱
│   │   └── deps.py             # 依赖注入
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 配置管理
│   │   ├── security.py         # 安全相关（JWT、密码）
│   │   └── celery_app.py       # Celery 配置
│   ├── db/                     # 数据库
│   │   ├── neo4j.py            # Neo4j 连接
│   │   ├── postgres.py         # PostgreSQL 连接
│   │   ├── redis.py            # Redis 连接
│   │   └── init_db.py          # 数据库初始化
│   ├── models/                 # 数据模型
│   │   ├── user.py             # 用户模型
│   │   ├── paper.py            # 论文模型
│   │   ├── conversation.py     # 对话模型
│   │   ├── task.py             # 任务模型
│   │   └── private_graph.py    # 私有图谱模型
│   ├── schemas/                # Pydantic schemas
│   │   ├── user.py
│   │   ├── graph.py
│   │   ├── chat.py
│   │   ├── paper.py
│   │   └── research.py
│   ├── services/               # 业务逻辑
│   │   ├── auth_service.py     # 认证服务
│   │   ├── graph_service.py    # 图谱服务
│   │   ├── chat_service.py     # 对话服务
│   │   ├── crawler_service.py  # 爬虫服务
│   │   ├── paper_service.py    # 论文服务
│   │   ├── reviewer_service.py # 审稿人服务
│   │   └── llm_service.py      # LLM 服务
│   ├── tasks/                  # Celery 任务
│   │   ├── crawler_tasks.py    # 爬虫任务
│   │   ├── research_tasks.py   # 调研任务
│   │   └── paper_tasks.py      # 论文处理任务
│   ├── utils/                  # 工具函数
│   │   ├── logger.py           # 日志
│   │   ├── pdf_parser.py       # PDF 解析
│   │   └── text_processor.py   # 文本处理
│   ├── crawlers/               # 爬虫模块
│   │   ├── arxiv_crawler.py    # arXiv 爬虫
│   │   ├── semantic_scholar.py # Semantic Scholar
│   │   ├── github_crawler.py   # GitHub 爬虫
│   │   └── base_crawler.py     # 爬虫基类
│   ├── middleware/             # 中间件
│   │   ├── cors.py             # CORS 配置
│   │   └── error_handler.py    # 错误处理
│   └── main.py                 # 应用入口
├── alembic/                    # 数据库迁移
│   ├── versions/
│   └── env.py
├── tests/                      # 测试
│   ├── api/
│   ├── services/
│   └── conftest.py
├── .env.example                # 环境变量示例
├── .env                        # 环境变量（不提交）
├── requirements.txt            # 依赖
├── alembic.ini                 # Alembic 配置
├── pytest.ini                  # Pytest 配置
└── BACKEND_REQUIREMENTS.md     # 本文件
```

---

## 功能模块详细需求

### 1. 用户认证模块 (`api/v1/auth.py`)

#### 1.1 用户注册
**接口**: `POST /api/v1/auth/register`

**请求体**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**功能**:
- 验证用户名唯一性
- 验证邮箱格式和唯一性
- 密码强度验证（至少 8 位，包含字母和数字）
- 密码哈希存储（bcrypt）
- 创建用户记录
- 返回 JWT Token

**数据库操作**:
- PostgreSQL: 插入用户记录

#### 1.2 用户登录
**接口**: `POST /api/v1/auth/login`

**请求体**:
```json
{
  "username_or_email": "string",
  "password": "string"
}
```

**功能**:
- 验证用户名/邮箱是否存在
- 验证密码
- 生成 JWT Token (有效期 7 天)
- 生成 Refresh Token (有效期 30 天)
- 返回用户信息和 Token

**响应**:
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user": {
    "id": "string",
    "username": "string",
    "email": "string"
  }
}
```

#### 1.3 Token 刷新
**接口**: `POST /api/v1/auth/refresh`

**请求头**:
```
Authorization: Bearer {refresh_token}
```

**功能**:
- 验证 Refresh Token
- 生成新的 Access Token

#### 1.4 获取当前用户
**接口**: `GET /api/v1/auth/me`

**功能**:
- 从 JWT Token 中提取用户信息
- 返回当前用户详情

---

### 2. 知识图谱模块 (`api/v1/graph.py`)

#### 2.1 获取子图
**接口**: `GET /api/v1/graph/subgraph`

**查询参数**:
```
query: string (关键词)
node_type: string (PAPER|PERSON|ORGANIZATION|CODE)
depth: int (深度，默认 2)
limit: int (节点数量限制，默认 100)
```

**功能**:
- 根据关键词在 Neo4j 中查询相关节点
- 提取指定深度的子图
- 限制节点数量（防止返回过大图谱）
- 返回节点和边的数据

**响应**:
```json
{
  "nodes": [
    {
      "id": "string",
      "type": "PAPER",
      "label": "string",
      "properties": {
        "title": "string",
        "authors": ["string"],
        "year": 2024,
        "citations": 100
      }
    }
  ],
  "edges": [
    {
      "id": "string",
      "source": "string",
      "target": "string",
      "type": "CITES"
    }
  ]
}
```

**Neo4j 查询示例**:
```cypher
MATCH (n:Paper)
WHERE n.title CONTAINS $query
MATCH path = (n)-[*1..2]-(related)
RETURN n, relationships(path), related
LIMIT 100
```

#### 2.2 获取节点详情
**接口**: `GET /api/v1/graph/node/{node_id}`

**功能**:
- 查询节点的所有属性
- 查询节点的直接关系
- 返回节点详细信息

#### 2.3 搜索节点
**接口**: `GET /api/v1/graph/search`

**查询参数**:
```
q: string (搜索关键词)
type: string (节点类型)
```

**功能**:
- 全文搜索节点
- 支持模糊匹配
- 返回匹配的节点列表

---

### 3. 爬虫与知识图谱维护模块 (`services/crawler_service.py`)

#### 3.1 arXiv 爬虫
**功能**:
- 根据关键词搜索 arXiv 论文
- 解析论文元数据（标题、作者、摘要、PDF 链接）
- 将论文节点写入 Neo4j
- 创建作者节点和 AUTHORED_BY 关系

**API**:
- arXiv API: `http://export.arxiv.org/api/query?search_query=xxx`

**数据写入**:
```cypher
MERGE (p:Paper {arxiv_id: $arxiv_id})
SET p.title = $title, p.abstract = $abstract, p.year = $year
MERGE (a:Person {name: $author_name})
MERGE (a)-[:AUTHORED]->(p)
```

#### 3.2 Semantic Scholar 爬虫
**功能**:
- 使用 Semantic Scholar API 获取论文信息
- 获取引用关系
- 获取作者信息和机构信息

**API**:
- Semantic Scholar API: `https://api.semanticscholar.org/graph/v1/paper/{paperId}`

**数据写入**:
- 创建 Paper 节点
- 创建 CITES 关系（引用关系）
- 创建 Person 和 Organization 节点

#### 3.3 GitHub 爬虫
**功能**:
- 爬取指定研究者的 GitHub 项目
- 解析项目元数据（语言、星标数、描述）
- 创建 Code 节点

**API**:
- GitHub API: `https://api.github.com/users/{username}/repos`

**数据写入**:
```cypher
MERGE (c:Code {github_url: $url})
SET c.name = $name, c.description = $description, c.stars = $stars
MERGE (p:Person {github_username: $username})
MERGE (p)-[:DEVELOPED]->(c)
```

#### 3.4 爬虫任务调度
**功能**:
- 使用 Celery 异步执行爬虫任务
- 记录爬虫进度
- 支持暂停/恢复
- 错误重试机制

**Celery 任务**:
```python
@celery_app.task
def crawl_arxiv(query: str, max_results: int = 100):
    # 爬取逻辑
    pass
```

---

### 4. 对话模块 (`api/v1/chat.py`)

#### 4.1 发送消息
**接口**: `POST /api/v1/chat/send`

**请求体**:
```json
{
  "message": "string",
  "session_id": "string"  // 可选，用于多轮对话
}
```

**功能**:
- 接收用户消息
- 查询知识图谱获取相关上下文
- 调用 DeepSeek API 生成回复
- 保存对话历史到 PostgreSQL
- 返回 AI 回复和引用文献

**响应**:
```json
{
  "message_id": "string",
  "content": "string",
  "references": [
    {
      "type": "paper",
      "id": "string",
      "title": "string",
      "url": "string"
    }
  ],
  "session_id": "string"
}
```

**流式响应（可选）**:
- 使用 Server-Sent Events (SSE)
- 实时返回生成的文本

**接口**: `GET /api/v1/chat/stream?message=xxx&session_id=xxx`

#### 4.2 获取对话历史
**接口**: `GET /api/v1/chat/history`

**查询参数**:
```
session_id: string
limit: int (默认 50)
```

**功能**:
- 查询数据库中的对话记录
- 按时间倒序返回

---

### 5. 调研功能模块 (`api/v1/research.py`)

#### 5.1 启动调研任务
**接口**: `POST /api/v1/research/start`

**请求体**:
```json
{
  "query": "string",  // 研究方向关键词
  "sources": ["arxiv", "semantic_scholar"],  // 数据源
  "max_papers": 50
}
```

**功能**:
- 创建异步爬虫任务（Celery）
- 返回 task_id

**响应**:
```json
{
  "task_id": "string",
  "status": "pending"
}
```

#### 5.2 查询任务进度
**接口**: `GET /api/v1/research/status/{task_id}`

**功能**:
- 查询 Celery 任务状态
- 返回进度信息

**响应**:
```json
{
  "task_id": "string",
  "status": "running",  // pending|running|completed|failed
  "progress": 75,       // 0-100
  "current_step": "正在爬取 Semantic Scholar..."
}
```

#### 5.3 获取调研结果
**接口**: `GET /api/v1/research/result/{task_id}`

**功能**:
- 提取相关子图
- 使用 DeepSeek 生成总结
- 返回文献列表和总结

**响应**:
```json
{
  "summary": "string",  // AI 生成的总结
  "papers": [...],
  "researchers": [...],
  "graph": {
    "nodes": [...],
    "edges": [...]
  }
}
```

---

### 6. Idea 检验模块 (`api/v1/idea.py`)

#### 6.1 验证 Idea
**接口**: `POST /api/v1/idea/validate`

**请求体**:
```json
{
  "idea": "string"  // Idea 描述
}
```

**功能**:
1. 使用 DeepSeek 理解 Idea
2. 提取关键词
3. 搜索相关文献
4. 使用 DeepSeek 评估可行性
5. 返回相关文献和评估结果

**响应**:
```json
{
  "understanding": "string",  // AI 对 Idea 的理解
  "related_papers": [...],
  "feasibility": {
    "score": 0.8,  // 可行性评分 0-1
    "pros": ["..."],
    "cons": ["..."],
    "suggestions": ["..."]
  }
}
```

---

### 7. 论文打磨模块 (`api/v1/paper.py`)

#### 7.1 上传论文
**接口**: `POST /api/v1/paper/upload`

**请求**:
- Content-Type: multipart/form-data
- file: PDF 文件

**功能**:
- 接收 PDF 文件
- 解析 PDF 文本（pdfplumber）
- 保存到文件系统或对象存储
- 创建 Paper 记录

**响应**:
```json
{
  "paper_id": "string",
  "filename": "string",
  "status": "uploaded"
}
```

#### 7.2 推荐审稿人
**接口**: `GET /api/v1/paper/{paper_id}/reviewers`

**功能**:
1. 分析论文内容（提取关键词、领域）
2. 从知识图谱中查询相关研究者
3. 根据研究者的论文历史生成画像
4. 返回审稿人列表

**响应**:
```json
{
  "reviewers": [
    {
      "id": "string",
      "name": "string",
      "affiliation": "string",
      "expertise": ["keyword1", "keyword2"],
      "representative_papers": [...],
      "profile": "string"  // AI 生成的画像
    }
  ]
}
```

**Neo4j 查询示例**:
```cypher
MATCH (p:Paper {id: $paper_id})
MATCH (related:Paper)-[:CITES*1..2]-(p)
MATCH (reviewer:Person)-[:AUTHORED]->(related)
RETURN reviewer, COUNT(related) as relevance
ORDER BY relevance DESC
LIMIT 10
```

#### 7.3 生成审稿意见
**接口**: `POST /api/v1/paper/{paper_id}/review`

**请求体**:
```json
{
  "reviewer_ids": ["string"]  // 选定的审稿人
}
```

**功能**:
1. 获取论文内容
2. 获取审稿人画像
3. 使用 DeepSeek 生成审稿意见（基于审稿人画像）
4. 返回审稿意见

**响应**:
```json
{
  "reviews": [
    {
      "reviewer_id": "string",
      "reviewer_name": "string",
      "comments": {
        "strengths": ["..."],
        "weaknesses": ["..."],
        "suggestions": ["..."]
      },
      "overall_score": 7  // 1-10
    }
  ]
}
```

**DeepSeek Prompt 示例**:
```
你是一位名为 {reviewer_name} 的审稿人。
你的研究方向是 {expertise}。
你曾发表过 {representative_papers}。
根据你的研究背景，请对以下论文进行评审：

{paper_content}

请从以下几个方面给出意见：
1. 优点
2. 缺点
3. 改进建议
```

#### 7.4 生成修改建议
**接口**: `POST /api/v1/paper/{paper_id}/suggestions`

**功能**:
1. 读取审稿意见
2. 使用 DeepSeek 生成针对性修改建议
3. 返回修改建议

**响应**:
```json
{
  "suggestions": [
    {
      "section": "Introduction",
      "original": "...",
      "suggestion": "...",
      "reason": "..."
    }
  ]
}
```

#### 7.5 版本管理
**接口**: `GET /api/v1/paper/{paper_id}/versions`

**功能**:
- 返回论文的所有版本
- 支持版本对比

---

### 8. 私有知识图谱模块 (`api/v1/private_graph.py`)

#### 8.1 创建私有图谱
**接口**: `POST /api/v1/private-graph`

**请求体**:
```json
{
  "name": "string",
  "description": "string"
}
```

**功能**:
- 在 Neo4j 中创建独立的私有图谱（使用标签区分）
- 关联到当前用户

#### 8.2 添加节点
**接口**: `POST /api/v1/private-graph/{graph_id}/node`

**请求体**:
```json
{
  "type": "PAPER",
  "properties": {
    "title": "...",
    "authors": ["..."]
  }
}
```

**功能**:
- 在私有图谱中添加节点
- 标记为 `:Private` 标签

#### 8.3 添加关系
**接口**: `POST /api/v1/private-graph/{graph_id}/edge`

**请求体**:
```json
{
  "source_id": "string",
  "target_id": "string",
  "type": "CITES"
}
```

#### 8.4 查询私有图谱
**接口**: `GET /api/v1/private-graph/{graph_id}`

**功能**:
- 返回私有图谱的所有节点和边
- 支持与公有图谱合并查询

---

## 服务层设计

### LLM 服务 (`services/llm_service.py`)

```python
class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1"
        )

    def chat(self, messages: List[Dict], stream: bool = False):
        """调用 DeepSeek API"""
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=stream
        )
        return response

    def generate_summary(self, context: str) -> str:
        """生成总结"""
        pass

    def evaluate_idea(self, idea: str, papers: List[str]) -> Dict:
        """评估 Idea 可行性"""
        pass

    def generate_review(self, paper: str, reviewer_profile: str) -> Dict:
        """生成审稿意见"""
        pass
```

### 图谱服务 (`services/graph_service.py`)

```python
class GraphService:
    def __init__(self):
        self.driver = neo4j_driver

    def get_subgraph(self, query: str, depth: int = 2, limit: int = 100):
        """获取子图"""
        pass

    def add_paper(self, paper_data: Dict):
        """添加论文节点"""
        pass

    def add_relationship(self, source_id: str, target_id: str, rel_type: str):
        """添加关系"""
        pass

    def search_nodes(self, query: str, node_type: str = None):
        """搜索节点"""
        pass
```

### 爬虫服务 (`services/crawler_service.py`)

```python
class CrawlerService:
    def crawl_arxiv(self, query: str, max_results: int = 100):
        """爬取 arXiv"""
        pass

    def crawl_semantic_scholar(self, query: str):
        """爬取 Semantic Scholar"""
        pass

    def crawl_github(self, username: str):
        """爬取 GitHub"""
        pass
```

---

## 数据库模型

### PostgreSQL 模型

#### User Model (`models/user.py`)
```python
class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    deepseek_api_key = Column(String, nullable=True)  # 用户自己的 API Key
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Conversation Model
```python
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    session_id = Column(String, nullable=False)
    role = Column(Enum("user", "assistant", "system"))
    content = Column(Text)
    references = Column(JSON)  # 引用的文献
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### Paper Model
```python
class Paper(Base):
    __tablename__ = "papers"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    filename = Column(String)
    file_path = Column(String)
    content = Column(Text)  # 解析后的文本
    status = Column(String)  # uploaded|processing|completed
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Neo4j 节点和关系

#### 节点类型
- `:Paper` - 论文
- `:Person` - 人物
- `:Organization` - 机构
- `:Code` - 代码项目
- `:Private` - 私有节点标签

#### 关系类型
- `:AUTHORED` - 作者关系
- `:CITES` - 引用关系
- `:WORKS_AT` - 工作于
- `:DEVELOPED` - 开发了
- `:BELONGS_TO` - 属于

---

## 安全与认证

### JWT 配置
- 算法: HS256
- Access Token 有效期: 7 天
- Refresh Token 有效期: 30 天
- Secret Key: 从环境变量读取

### 权限控制
- 使用 FastAPI Depends 进行依赖注入
- 中间件验证 Token

```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401)
        return user_id
    except JWTError:
        raise HTTPException(status_code=401)
```

### 密码安全
- 使用 bcrypt 哈希
- 加盐存储

---

## 错误处理

### 统一错误响应格式
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "用户名已存在",
    "details": {}
  }
}
```

### 错误码定义
- `INVALID_INPUT` - 输入验证失败
- `UNAUTHORIZED` - 未认证
- `FORBIDDEN` - 无权限
- `NOT_FOUND` - 资源不存在
- `INTERNAL_ERROR` - 服务器错误

---

## 性能优化

### 1. 数据库优化
- Neo4j 索引：在常用属性上建立索引（title, arxiv_id 等）
- PostgreSQL 索引：user_id, session_id
- 连接池配置

### 2. 缓存策略
- Redis 缓存常见查询结果
- 缓存 DeepSeek API 响应（相同问题）
- TTL: 1 小时

### 3. 异步处理
- 使用 Celery 处理耗时任务（爬虫、AI 生成）
- 使用 asyncio 处理并发请求

### 4. 限流
- 使用 slowapi 限制 API 请求频率
- 每用户每分钟最多 60 次请求

---

## 日志

### 日志级别
- DEBUG: 开发环境详细日志
- INFO: 常规操作日志
- WARNING: 警告信息
- ERROR: 错误信息

### 日志内容
- API 请求日志（URL, 方法, 用户, 响应时间）
- 错误堆栈
- 爬虫任务日志
- LLM API 调用日志

---

## 测试

### 单元测试
```bash
pytest tests/
```

### 测试覆盖
- API 路由测试
- 服务层逻辑测试
- 数据库操作测试

### 测试数据库
- 使用独立的测试数据库
- 每次测试后清理数据

---

## 部署

### 环境变量 (`.env`)
```
# 数据库
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
POSTGRES_URI=postgresql://user:password@localhost/radiant
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256

# DeepSeek API
DEEPSEEK_API_KEY=your-api-key

# 文件存储
UPLOAD_DIR=/path/to/uploads
```

### 启动命令
```bash
# 开发环境
uvicorn app.main:app --reload

# 生产环境
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# Celery Beat (定时任务)
celery -A app.core.celery_app beat --loglevel=info
```

---

## 开发规范

### 代码风格
- 遵循 PEP 8
- 使用 Black 格式化代码
- 使用 isort 排序导入

### 类型注解
- 所有函数必须有类型注解
- 使用 Pydantic 验证数据

### 文档
- 所有 API 使用 FastAPI 自动生成文档
- 复杂函数添加 docstring

---

## 待开发功能清单

### Phase 1（基础功能）
- [ ] 用户认证 API
- [ ] 知识图谱 CRUD API
- [ ] Neo4j 连接和基础查询
- [ ] PostgreSQL 模型设计

### Phase 2（爬虫功能）
- [ ] arXiv 爬虫
- [ ] Semantic Scholar 爬虫
- [ ] GitHub 爬虫
- [ ] Celery 任务队列

### Phase 3（AI 功能）
- [ ] DeepSeek API 集成
- [ ] 对话服务
- [ ] 审稿人画像生成
- [ ] 论文修改建议生成

### Phase 4（高级功能）
- [ ] 私有知识图谱
- [ ] 流式响应
- [ ] 性能优化
- [ ] 监控和日志
