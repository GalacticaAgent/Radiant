-- Radiant 项目 PostgreSQL 数据库初始化脚本
-- 创建必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    deepseek_api_key VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- 2. 对话表
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    ref_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);

-- 2.1 会话元数据表
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(100) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_updated_at ON chat_sessions(updated_at DESC);

-- 3. 论文文件表
CREATE TABLE IF NOT EXISTS papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    content TEXT,
    abstract TEXT,
    paper_metadata JSONB,
    version INTEGER DEFAULT 1,
    parent_id UUID REFERENCES papers(id),
    status VARCHAR(20) DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_papers_user_id ON papers(user_id);
CREATE INDEX idx_papers_status ON papers(status);

-- 3.1 审稿意见表（与后端 ORM 的 paper_reviews 对齐）
CREATE TABLE IF NOT EXISTS paper_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reviewer_id VARCHAR(100),
    reviewer_name VARCHAR(200),
    reviewer_profile TEXT,
    review_content TEXT NOT NULL,
    rating INTEGER,
    strengths TEXT[],
    weaknesses TEXT[],
    suggestions TEXT[],
    review_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_paper_reviews_paper_id ON paper_reviews(paper_id);
CREATE INDEX idx_paper_reviews_user_id ON paper_reviews(user_id);

-- 3.2 虚拟审稿人表（基于公开信息生成的审稿人画像）
CREATE TABLE IF NOT EXISTS virtual_reviewers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,
    external_id VARCHAR(200) NOT NULL,
    name VARCHAR(200) NOT NULL,
    affiliation VARCHAR(500),
    h_index INTEGER,
    citation_count INTEGER,
    paper_count INTEGER,
    profile_text TEXT,
    top_papers JSONB,
    talk_links JSONB,
    raw_profile JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_virtual_reviewers_source_external_id UNIQUE (source, external_id)
);

CREATE INDEX idx_virtual_reviewers_name ON virtual_reviewers(name);
CREATE INDEX idx_virtual_reviewers_source ON virtual_reviewers(source);

-- 3.3 论文-候选审稿人缓存表
CREATE TABLE IF NOT EXISTS paper_reviewer_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES virtual_reviewers(id) ON DELETE CASCADE,
    rank INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    rationale VARCHAR(800),
    matched_keywords JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_paper_reviewer_candidates_paper_id_reviewer_id UNIQUE (paper_id, reviewer_id)
);

CREATE INDEX idx_paper_reviewer_candidates_paper_id ON paper_reviewer_candidates(paper_id);
CREATE INDEX idx_paper_reviewer_candidates_reviewer_id ON paper_reviewer_candidates(reviewer_id);

-- 3.4 知识库：作者与关联关系
CREATE TABLE IF NOT EXISTS authors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,
    external_id VARCHAR(200) NOT NULL,
    name VARCHAR(200) NOT NULL,
    aliases JSONB,
    affiliations JSONB,
    homepage TEXT,
    url TEXT,
    h_index INTEGER,
    citation_count INTEGER,
    paper_count INTEGER,
    raw_profile JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_authors_source_external_id UNIQUE (source, external_id)
);

CREATE INDEX idx_authors_name ON authors(name);
CREATE INDEX idx_authors_source ON authors(source);

CREATE TABLE IF NOT EXISTS paper_authors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    author_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_paper_authors_paper_id_author_id UNIQUE (paper_id, author_id)
);

CREATE INDEX idx_paper_authors_paper_id ON paper_authors(paper_id);
CREATE INDEX idx_paper_authors_author_id ON paper_authors(author_id);

-- 3.5 知识库：主题标签
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_topics_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS paper_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_paper_topics UNIQUE (paper_id, topic_id, source)
);

CREATE INDEX idx_paper_topics_paper_id ON paper_topics(paper_id);
CREATE INDEX idx_paper_topics_topic_id ON paper_topics(topic_id);

-- 3.6 知识库：向量/嵌入（pgvector）
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS external_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,
    external_id VARCHAR(200) NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    year INTEGER,
    venue TEXT,
    url TEXT,
    external_ids JSONB,
    fields_of_study JSONB,
    citation_count INTEGER,
    raw JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_external_papers_source_external_id UNIQUE (source, external_id)
);

CREATE INDEX idx_external_papers_title ON external_papers(title);
CREATE INDEX idx_external_papers_source ON external_papers(source);

CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    object_type VARCHAR(30) NOT NULL,
    object_id UUID NOT NULL,
    model VARCHAR(100) NOT NULL,
    dim INTEGER NOT NULL,
    vector vector(768),
    vector_jsonb JSONB,
    content_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_embeddings_object UNIQUE (object_type, object_id, model)
);

CREATE INDEX idx_embeddings_object ON embeddings(object_type, object_id);

-- 3.7 知识库：抓取/构建任务与事件
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(30) NOT NULL,
    target_id UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crawl_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crawl_jobs_target ON crawl_jobs(target_type, target_id);
CREATE INDEX idx_crawl_events_job_id ON crawl_events(job_id);

-- 4. 论文版本表
CREATE TABLE IF NOT EXISTS paper_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    changes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_paper_versions_paper_id ON paper_versions(paper_id);
CREATE UNIQUE INDEX idx_paper_version_unique ON paper_versions(paper_id, version_number);

-- 5. 审稿意见表
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    reviewer_id VARCHAR(100),
    reviewer_name VARCHAR(100),
    comments JSONB NOT NULL,
    overall_score INTEGER CHECK (overall_score BETWEEN 1 AND 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reviews_paper_id ON reviews(paper_id);

-- 6. 调研任务表
CREATE TABLE IF NOT EXISTS research_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id VARCHAR(100) UNIQUE NOT NULL,
    query VARCHAR(500) NOT NULL,
    sources JSONB,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    progress INTEGER DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_research_tasks_user_id ON research_tasks(user_id);
CREATE INDEX idx_research_tasks_task_id ON research_tasks(task_id);

-- 7. 私有知识图谱表
CREATE TABLE IF NOT EXISTS private_graphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_private_graphs_user_id ON private_graphs(user_id);

-- 8. API 使用记录表
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    api_type VARCHAR(50) NOT NULL,
    tokens_used INTEGER,
    cost DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX idx_api_usage_created_at ON api_usage(created_at DESC);

-- 创建触发器函数 - 自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为各表添加触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_papers_updated_at BEFORE UPDATE ON papers
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_research_tasks_updated_at BEFORE UPDATE ON research_tasks
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_private_graphs_updated_at BEFORE UPDATE ON private_graphs
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入初始管理员用户（可选）
-- 密码为 'admin123' 的 bcrypt 哈希值
INSERT INTO users (username, email, hashed_password, is_superuser)
VALUES ('admin', 'admin@radiant.com', '$2b$12$n3jHnuWW0XGF3CjRZAT.uOg9WfaLe1R6eXSvl.vQqvvVR5VlNnUu.', TRUE)
ON CONFLICT (username) DO NOTHING;
