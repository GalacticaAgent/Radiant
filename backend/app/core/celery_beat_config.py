"""
Celery Beat 定时任务配置
"""

from celery.schedules import crontab


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

# Celery 配置
celery_config = {
    'beat_schedule': beat_schedule,
    'timezone': 'UTC',
    'enable_utc': True,
}
