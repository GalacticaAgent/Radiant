"""
Celery 应用配置
用于异步任务处理（爬虫、邮件等）
"""

from celery import Celery
from app.core.config import settings
from celery.schedules import crontab

# 创建 Celery 应用
celery_app = Celery(
    "radiant",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.set_default()

# Beat 定时任务配置
beat_schedule = {
    # 每天凌晨2点爬取热门论文
    'crawl-hot-papers-daily': {
        'task': 'crawl_hot_papers',
        'schedule': crontab(hour=2, minute=0),
        'args': (50,),  # 每天爬取50篇
    },
    # 每6小时更新一次图谱统计
    'update-graph-stats': {
        'task': 'update_graph_stats',
        'schedule': crontab(minute=0, hour='*/6'),
    },
}

_seed_domains = [x.strip() for x in (getattr(settings, "KB_SEED_DOMAINS", "") or "").split(",") if x.strip()]
if _seed_domains:
    for idx, dom in enumerate(_seed_domains):
        beat_schedule[f"kb-seed-domain-experts-{idx}"] = {
            "task": "kb_seed_domain_experts",
            "schedule": crontab(hour=3, minute=30),
            "args": (dom, int(getattr(settings, "KB_SEED_DOMAIN_PER_PAGE", 25)), int(getattr(settings, "KB_SEED_DOMAIN_MAX_AUTHORS", 200))),
        }

# 配置 Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 分钟
    task_soft_time_limit=25 * 60,  # 25 分钟
    worker_max_tasks_per_child=1000,  # 每个 worker 最多执行 1000 个任务后重启
    broker_connection_retry_on_startup=True,  # 启动时重试连接到 broker
    beat_schedule=beat_schedule,  # 定时任务配置
)

# 自动发现任务
celery_app.autodiscover_tasks(["app"])
