# 部署手册（格式审查模块）

## 依赖
- Postgres（当前 compose 已包含）
- Redis（当前 compose 已包含，用于任务队列/进度缓存）
- Celery worker（执行格式审查、规则生成、一键修改等任务）

## 环境变量
- 后端：`backend/.env`
  - `MAX_UPLOAD_SIZE`：默认 50MB
  - `VIRUS_SCAN_ENABLED`：是否启用 ClamAV 扫描（默认 false）
  - `CLAMAV_COMMAND`：ClamAV 扫描命令（默认 clamscan）

## 启动顺序
1. 启动数据库与 Redis（docker compose）
2. 启动后端 FastAPI（uvicorn）
3. 启动 Celery worker（需与后端同一代码环境）
4. 启动前端（vite dev / build + preview）

## 访问入口
- 前端：进入聊天页，点击“格式审查”进入 `/format-review/:sessionId` 看板
- 后端接口：`/docs` 查看 OpenAPI

