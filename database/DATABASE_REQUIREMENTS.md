# 数据库设计文档

## 数据库架构概述

Radiant 项目采用多数据库架构，充分利用不同数据库的优势：

- **Neo4j**：存储知识图谱（论文、研究者、代码项目及其关系）
- **PostgreSQL**：存储用户数据、配置、对话历史等结构化数据
- **Redis**：缓存、消息队列、会话存储

---

## 1. Neo4j 图数据库设计

### 1.1 节点类型 (Node Labels)

#### Paper（论文节点）
**标签**: `:Paper`

**属性**:
```
id: String (唯一标识符)
title: String (论文标题)
abstract: Text (摘要)
arxiv_id: String (arXiv ID，可选)
doi: String (DOI，可选)
url: String (论文链接)
year: Integer (发表年份)
venue: String (发表会议/期刊)
citations: Integer (引用次数)
pdf_url: String (PDF 下载链接)
keywords: List<String> (关键词)
created_at: DateTime (创建时间)
updated_at: DateTime (更新时间)
```

**索引**:
```cypher
CREATE INDEX paper_title IF NOT EXISTS FOR (p:Paper) ON (p.title);
CREATE INDEX paper_arxiv_id IF NOT EXISTS FOR (p:Paper) ON (p.arxiv_id);
CREATE INDEX paper_year IF NOT EXISTS FOR (p:Paper) ON (p.year);
CREATE FULLTEXT INDEX paper_fulltext IF NOT EXISTS FOR (p:Paper) ON EACH [p.title, p.abstract];
```

#### Person（人物节点 - 研究者）
**标签**: `:Person`

**属性**:
```
id: String
name: String (姓名)
email: String (邮箱，可选)
affiliation: String (所属机构)
homepage: String (个人主页)
github_username: String (GitHub 用户名)
google_scholar_id: String (Google Scholar ID)
research_interests: List<String> (研究方向)
h_index: Integer (H-index)
created_at: DateTime
updated_at: DateTime
```

**索引**:
```cypher
CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX person_email IF NOT EXISTS FOR (p:Person) ON (p.email);
```

#### Organization（机构节点）
**标签**: `:Organization`

**属性**:
```
id: String
name: String (机构名称)
type: String (university|company|research_institute)
country: String (国家)
website: String (官网)
created_at: DateTime
```

**索引**:
```cypher
CREATE INDEX org_name IF NOT EXISTS FOR (o:Organization) ON (o.name);
```

#### Code（代码项目节点）
**标签**: `:Code`

**属性**:
```
id: String
name: String (项目名称)
description: Text (项目描述)
github_url: String (GitHub 链接)
language: String (主要编程语言)
stars: Integer (星标数)
forks: Integer (Fork 数)
topics: List<String> (主题标签)
created_at: DateTime
updated_at: DateTime
```

**索引**:
```cypher
CREATE INDEX code_github_url IF NOT EXISTS FOR (c:Code) ON (c.github_url);
```

#### Private（私有节点标签）
**标签**: `:Private`

用于标记用户的私有知识图谱节点，配合 `user_id` 属性使用。

**附加属性**:
```
user_id: String (所属用户 ID)
```

---

### 1.2 关系类型 (Relationships)

#### AUTHORED（作者关系）
**类型**: `(Person)-[:AUTHORED]->(Paper)`

**属性**:
```
position: Integer (作者顺序，1 表示第一作者)
```

**示例**:
```cypher
MATCH (p:Person {name: "Alice"}), (paper:Paper {title: "Deep Learning"})
CREATE (p)-[:AUTHORED {position: 1}]->(paper)
```

#### CITES（引用关系）
**类型**: `(Paper)-[:CITES]->(Paper)`

**属性**:
```
context: String (引用上下文，可选)
```

**示例**:
```cypher
MATCH (p1:Paper {title: "Paper A"}), (p2:Paper {title: "Paper B"})
CREATE (p1)-[:CITES]->(p2)
```

#### WORKS_AT（工作关系）
**类型**: `(Person)-[:WORKS_AT]->(Organization)`

**属性**:
```
position: String (职位)
start_year: Integer (开始年份)
end_year: Integer (结束年份，可选)
```

#### DEVELOPED（开发关系）
**类型**: `(Person)-[:DEVELOPED]->(Code)`

**属性**:
```
role: String (角色：owner|contributor|maintainer)
```

#### IMPLEMENTS（实现关系）
**类型**: `(Code)-[:IMPLEMENTS]->(Paper)`

表示代码项目实现了某篇论文的方法。

#### BELONGS_TO（归属关系）
**类型**: `(Paper)-[:BELONGS_TO]->(Organization)`

表示论文归属于某个机构。

#### CO_AUTHOR（合作关系）
**类型**: `(Person)-[:CO_AUTHOR]->(Person)`

**属性**:
```
collaboration_count: Integer (合作次数)
```

可通过查询共同作者论文动态生成。

---

### 1.3 知识图谱设计原则

#### 数据去重
- 使用 `MERGE` 而非 `CREATE` 避免重复节点
- 通过唯一属性（如 `arxiv_id`, `email`）进行匹配

#### 关系建模
- 优先使用有向关系
- 关系类型使用大写蛇形命名（如 `AUTHORED`）
- 复杂关系使用属性存储元数据

#### 性能优化
- 为高频查询字段建立索引
- 限制遍历深度（建议不超过 3）
- 使用 `LIMIT` 限制返回结果数量

---

### 1.4 常用 Cypher 查询

#### 查询研究者的所有论文
```cypher
MATCH (p:Person {name: $name})-[:AUTHORED]->(paper:Paper)
RETURN paper
ORDER BY paper.year DESC
```

#### 查询论文的引用网络（2 层深度）
```cypher
MATCH path = (p:Paper {title: $title})-[:CITES*1..2]-(related:Paper)
RETURN p, relationships(path), related
LIMIT 100
```

#### 查询研究者的合作网络
```cypher
MATCH (p1:Person {name: $name})-[:AUTHORED]->(paper:Paper)<-[:AUTHORED]-(p2:Person)
WHERE p1 <> p2
RETURN p2, COUNT(paper) as collaboration_count
ORDER BY collaboration_count DESC
```

#### 查询某领域的顶级论文
```cypher
MATCH (p:Paper)
WHERE ANY(keyword IN p.keywords WHERE keyword CONTAINS $field)
RETURN p
ORDER BY p.citations DESC
LIMIT 20
```

#### 子图提取（关键词搜索）
```cypher
MATCH (p:Paper)
WHERE p.title CONTAINS $query OR p.abstract CONTAINS $query
WITH p LIMIT 50
MATCH path = (p)-[*1..2]-(related)
RETURN p, relationships(path), related
```

#### 私有图谱查询（结合公有图谱）
```cypher
MATCH (n)
WHERE (n:Private AND n.user_id = $user_id) OR NOT n:Private
MATCH path = (n)-[*1..2]-(related)
RETURN n, relationships(path), related
LIMIT 100
```

---

## 2. PostgreSQL 关系数据库设计

### 2.1 表结构设计

#### users（用户表）
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    deepseek_api_key VARCHAR(255),  -- 用户自己的 DeepSeek API Key
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

#### conversations（对话表）
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    references JSONB,  -- 引用的文献，格式：[{"type": "paper", "id": "...", "title": "..."}]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
```

#### papers（论文文件表）
```sql
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,  -- 文件大小（字节）
    content TEXT,  -- 解析后的文本内容
    metadata JSONB,  -- 论文元数据（标题、作者等）
    status VARCHAR(20) DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_papers_user_id ON papers(user_id);
CREATE INDEX idx_papers_status ON papers(status);
```

#### paper_versions（论文版本表）
```sql
CREATE TABLE paper_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    changes JSONB,  -- 修改说明
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_paper_versions_paper_id ON paper_versions(paper_id);
CREATE UNIQUE INDEX idx_paper_version_unique ON paper_versions(paper_id, version_number);
```

#### reviews（审稿意见表）
```sql
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    reviewer_id VARCHAR(100),  -- Neo4j 中的 Person 节点 ID
    reviewer_name VARCHAR(100),
    comments JSONB NOT NULL,  -- 审稿意见，格式：{"strengths": [...], "weaknesses": [...], "suggestions": [...]}
    overall_score INTEGER CHECK (overall_score BETWEEN 1 AND 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reviews_paper_id ON reviews(paper_id);
```

#### research_tasks（调研任务表）
```sql
CREATE TABLE research_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id VARCHAR(100) UNIQUE NOT NULL,  -- Celery Task ID
    query VARCHAR(500) NOT NULL,
    sources JSONB,  -- 数据源：["arxiv", "semantic_scholar"]
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    progress INTEGER DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    result JSONB,  -- 调研结果
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_research_tasks_user_id ON research_tasks(user_id);
CREATE INDEX idx_research_tasks_task_id ON research_tasks(task_id);
```

#### private_graphs（私有知识图谱表）
```sql
CREATE TABLE private_graphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_private_graphs_user_id ON private_graphs(user_id);
```

#### api_usage（API 使用记录表）
```sql
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    api_type VARCHAR(50) NOT NULL,  -- deepseek|arxiv|semantic_scholar
    tokens_used INTEGER,  -- 使用的 token 数（针对 LLM API）
    cost DECIMAL(10, 6),  -- 费用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX idx_api_usage_created_at ON api_usage(created_at DESC);
```

---

### 2.2 触发器

#### 自动更新 updated_at
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_papers_updated_at BEFORE UPDATE ON papers
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_private_graphs_updated_at BEFORE UPDATE ON private_graphs
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### 2.3 常用 SQL 查询

#### 获取用户的对话历史
```sql
SELECT * FROM conversations
WHERE user_id = $1 AND session_id = $2
ORDER BY created_at ASC;
```

#### 获取论文的所有版本
```sql
SELECT * FROM paper_versions
WHERE paper_id = $1
ORDER BY version_number DESC;
```

#### 统计用户的 API 使用情况
```sql
SELECT api_type, COUNT(*) as count, SUM(tokens_used) as total_tokens
FROM api_usage
WHERE user_id = $1 AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY api_type;
```

---

## 3. Redis 缓存与队列

### 3.1 使用场景

#### 缓存
- **键格式**: `cache:{resource_type}:{id}`
- **示例**:
  - `cache:subgraph:query_hash` - 子图查询结果
  - `cache:paper:arxiv_id` - 论文详情
  - `cache:llm_response:prompt_hash` - LLM 响应缓存

#### 会话存储
- **键格式**: `session:{session_id}`
- **TTL**: 30 分钟
- **内容**: 用户会话信息（登录状态、上下文）

#### 任务队列
- **Celery Broker**: 使用 Redis 作为消息队列
- **Celery Backend**: 使用 Redis 存储任务结果

#### 限流
- **键格式**: `rate_limit:{user_id}:{endpoint}`
- **TTL**: 1 分钟
- **限制**: 每分钟 60 次请求

---

### 3.2 缓存策略

#### 缓存失效时间
- 子图查询: 1 小时
- 论文详情: 24 小时
- LLM 响应: 7 天
- 会话数据: 30 分钟

#### 缓存更新
- 写入时更新（Write-through）
- 定时刷新（针对爬虫数据）

---

## 4. 数据库初始化脚本

### 4.1 Neo4j 初始化 (`database/neo4j_init.cypher`)

```cypher
// 创建约束
CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT org_id_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT code_id_unique IF NOT EXISTS FOR (c:Code) REQUIRE c.id IS UNIQUE;

// 创建索引
CREATE INDEX paper_title IF NOT EXISTS FOR (p:Paper) ON (p.title);
CREATE INDEX paper_arxiv_id IF NOT EXISTS FOR (p:Paper) ON (p.arxiv_id);
CREATE INDEX paper_year IF NOT EXISTS FOR (p:Paper) ON (p.year);
CREATE FULLTEXT INDEX paper_fulltext IF NOT EXISTS FOR (p:Paper) ON EACH [p.title, p.abstract];

CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX org_name IF NOT EXISTS FOR (o:Organization) ON (o.name);
CREATE INDEX code_github_url IF NOT EXISTS FOR (c:Code) ON (c.github_url);

// 插入示例数据（可选）
CREATE (p:Paper {
    id: "paper-001",
    title: "Attention Is All You Need",
    abstract: "...",
    year: 2017,
    venue: "NeurIPS",
    citations: 50000
});

CREATE (author:Person {
    id: "person-001",
    name: "Ashish Vaswani",
    affiliation: "Google Brain"
});

CREATE (author)-[:AUTHORED {position: 1}]->(p);
```

---

### 4.2 PostgreSQL 初始化 (`database/postgres_init.sql`)

```sql
-- 执行上述所有 CREATE TABLE 语句
-- 执行触发器创建语句

-- 插入管理员用户（可选）
INSERT INTO users (username, email, hashed_password, is_superuser)
VALUES ('admin', 'admin@radiant.com', '$2b$12$...', TRUE);
```

---

## 5. 数据迁移

### 5.1 使用 Alembic 管理 PostgreSQL 迁移

#### 初始化
```bash
alembic init alembic
```

#### 创建迁移
```bash
alembic revision --autogenerate -m "Initial migration"
```

#### 执行迁移
```bash
alembic upgrade head
```

---

### 5.2 Neo4j 迁移策略

Neo4j 没有官方迁移工具，建议：
- 使用 Cypher 脚本管理 schema 变更
- 版本化管理迁移脚本（`migrations/neo4j/v1.cypher`）
- 在应用启动时检查并执行迁移

---

## 6. 数据备份与恢复

### 6.1 Neo4j 备份

#### 备份命令
```bash
neo4j-admin dump --database=neo4j --to=/backup/neo4j-backup.dump
```

#### 恢复命令
```bash
neo4j-admin load --from=/backup/neo4j-backup.dump --database=neo4j --force
```

#### 自动备份策略
- 每天凌晨 3 点自动备份
- 保留最近 7 天的备份
- 使用 cron job 调度

---

### 6.2 PostgreSQL 备份

#### 备份命令
```bash
pg_dump -U postgres -d radiant > backup.sql
```

#### 恢复命令
```bash
psql -U postgres -d radiant < backup.sql
```

---

### 6.3 Redis 备份

#### 持久化配置
在 `redis.conf` 中配置：
```
save 900 1      # 900秒内有1次写入
save 300 10     # 300秒内有10次写入
save 60 10000   # 60秒内有10000次写入
```

#### 备份 RDB 文件
```bash
cp /var/lib/redis/dump.rdb /backup/
```

---

## 7. 性能优化建议

### 7.1 Neo4j 优化
- 为高频查询字段建立索引
- 使用 `PROFILE` 分析查询性能
- 限制遍历深度（`[*1..2]` 而非 `[*]`）
- 使用 `LIMIT` 限制结果集大小
- 配置足够的堆内存（建议 8GB+）

### 7.2 PostgreSQL 优化
- 为外键和常用查询字段建立索引
- 使用 `EXPLAIN ANALYZE` 分析查询计划
- 定期执行 `VACUUM` 清理
- 配置连接池（如 pgbouncer）

### 7.3 Redis 优化
- 设置合理的 TTL
- 使用 Redis Cluster 处理大规模数据
- 监控内存使用

---

## 8. 监控与日志

### 8.1 数据库监控指标

#### Neo4j
- 查询响应时间
- 节点/边数量
- 内存使用
- 缓存命中率

#### PostgreSQL
- 查询响应时间
- 连接数
- 慢查询日志
- 表大小

#### Redis
- 内存使用
- 命中率
- 连接数

---

### 8.2 日志配置

#### Neo4j 日志
- 位置: `/var/log/neo4j/`
- 级别: INFO
- 慢查询阈值: 1000ms

#### PostgreSQL 日志
- 慢查询记录（> 1s）
- 错误日志

---

## 9. 安全考虑

### 9.1 访问控制
- Neo4j: 启用认证，创建只读用户（用于前端查询）
- PostgreSQL: 使用最小权限原则
- Redis: 启用密码认证

### 9.2 数据加密
- 敏感数据（密码、API Key）加密存储
- 数据库连接使用 SSL/TLS

### 9.3 SQL 注入防护
- 使用参数化查询
- 避免字符串拼接

---

## 10. 项目文件结构

```
database/
├── neo4j/
│   ├── init.cypher           # 初始化脚本
│   ├── indexes.cypher        # 索引创建
│   ├── constraints.cypher    # 约束创建
│   └── seed_data.cypher      # 种子数据
├── postgres/
│   ├── schema.sql            # 表结构
│   ├── triggers.sql          # 触发器
│   ├── indexes.sql           # 索引
│   └── seed_data.sql         # 种子数据
├── migrations/               # 迁移脚本
│   ├── neo4j/
│   │   ├── v1.cypher
│   │   └── v2.cypher
│   └── postgres/
│       └── alembic/
├── backup/                   # 备份脚本
│   ├── backup_neo4j.sh
│   ├── backup_postgres.sh
│   └── backup_redis.sh
├── scripts/                  # 工具脚本
│   ├── init_databases.py     # 初始化所有数据库
│   └── reset_databases.py    # 重置数据库（开发用）
└── DATABASE_REQUIREMENTS.md  # 本文件
```

---

## 11. 开发与测试

### 11.1 测试数据库
- 使用独立的测试数据库实例
- Neo4j: `neo4j-test`
- PostgreSQL: `radiant_test`
- Redis: 使用不同的 DB 编号（如 DB 1）

### 11.2 测试数据生成
- 使用 Faker 生成模拟数据
- 创建测试数据脚本（`scripts/generate_test_data.py`）

---

## 12. 待实现功能清单

### Phase 1（基础设施）
- [ ] Neo4j 数据库部署
- [ ] PostgreSQL 数据库部署
- [ ] Redis 部署
- [ ] 初始化脚本编写

### Phase 2（Schema 设计）
- [ ] Neo4j 节点和关系设计
- [ ] PostgreSQL 表结构设计
- [ ] 索引和约束创建

### Phase 3（数据迁移）
- [ ] Alembic 配置
- [ ] 迁移脚本编写

### Phase 4（优化与监控）
- [ ] 性能优化
- [ ] 备份脚本
- [ ] 监控配置
