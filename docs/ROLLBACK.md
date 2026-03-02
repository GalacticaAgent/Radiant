# 回滚方案（格式审查模块）

## 前端回滚
- 回滚路由与入口：撤销 `/format-review/:sessionId` 路由与 ChatBox 中的跳转逻辑，恢复原 FormatReviewModal 入口。
- 若仅回滚功能但保留页面：可以将入口按钮回退到旧行为，保留新页面不入口。

## 后端回滚
- 新增路由均为 `/api/*` 前缀，不影响现有 `/api/v1/*` 旧接口；若需回滚只需移除：
  - `app/api/format_review.py`
  - `app/api/upload.py`
  - `app/api/rule.py`
  - 以及 `main.py` 中 include_router 的挂载
- 数据库表为新增表：`format_review_*`、`format_rule_*`、`download_tokens`。回滚时可保留不使用或手动删除表。

## 风险点
- 若启用 ClamAV：回滚时应同步关闭 `VIRUS_SCAN_ENABLED`，避免部署缺少 clamscan 导致上传失败。

