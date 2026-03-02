from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 项目信息
    PROJECT_NAME: str = "Radiant"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # 安全
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # 数据库
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "radiant"

    @property
    def POSTGRES_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    REDIS_URL: str = "redis://localhost:6379/0"

    # DeepSeek API
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    FORMAT_AUTOFIX_ENABLED: bool = True

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_RUN_INLINE: bool = True

    # 爬虫配置
    GITHUB_TOKEN: Optional[str] = None
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None
    CRAWLER_USER_AGENT: str = "Radiant-Academic-Assistant/1.0"
    CRAWLER_MAX_RETRY: int = 3
    CRAWLER_DELAY: int = 1
    CRAWLER_SCHEDULE_ENABLED: bool = True
    CRAWLER_DAILY_LIMIT: int = 50

    # Embedding / Vector Index（MVP 先落库 JSONB，后续可迁移 pgvector）
    EMBEDDING_ENABLED: bool = False
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_BASE_URL: Optional[str] = None
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

    PGVECTOR_ENABLED: bool = False
    PGVECTOR_DIM: int = 1536

    KB_SEED_DOMAINS: str = ""
    KB_SEED_DOMAIN_PER_PAGE: int = 25
    KB_SEED_DOMAIN_MAX_AUTHORS: int = 200

    VIRUS_SCAN_ENABLED: bool = False
    CLAMAV_COMMAND: str = "clamscan"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
