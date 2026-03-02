# 格式审查模块 API（OpenAPI 由 /docs 自动生成）

说明：本仓库后端当前为 FastAPI（Python），新接口统一返回 `{code,msg,data}`，并通过响应头 `X-Trace-Id` 透传链路追踪标识。

## 上传（分片）

### POST /api/upload/init
- 入参：`{ session_id, filename, size, mime_type }`
- 出参：`{ upload_id, chunk_size }`

### PUT /api/upload/{uploadId}/part?part_number=1
- Body：二进制分片（application/octet-stream）

### POST /api/upload/{uploadId}/complete
- 服务端校验：扩展名白名单、文件头魔数、敏感内容检测、（可选）ClamAV 扫描

### GET /api/upload/{uploadId}/status
- 返回已上传 part 列表，用于断点续传

## 格式审查任务

### POST /api/format-review/start
- 入参：`{ session_id, upload_id?, rule_id? }`
- 出参：`{ task_id }`
- 约束：
  - `upload_id` 对应上传必须为 `ready` 状态
  - `.doc` 当前仅完成魔数校验与存储，审查解析建议使用 `.pdf/.docx`

### GET /api/format-review/task/{taskId}
- 返回任务状态、进度、结果

### GET /api/format-review/task/{taskId}/stream
- SSE 进度推送（query token 鉴权）

### POST /api/format-review/history/save
- 入参：`{ task_id }`
- 出参：`{ history_id }`

### GET /api/format-review/history?session_id=...&page=1&page_size=10&q=...
- 会话维度历史列表（分页 + 关键词搜索）

### DELETE /api/format-review/history/{historyId}
- 删除单条历史

## 一键修改与下载

### POST /api/format-review/auto-fix
- 入参：`{ history_id }`
- 出参：`{ fix_task_id }`

### GET /api/format-review/auto-fix/{fixTaskId}
- 返回状态与 `download_url`

### GET /api/format-review/download/{token}
- 一次性下载链接（7 天过期，下载后失效）

## 规则管理

### POST /api/rule/upload
- 上传规则文档（≤20MB，.pdf/.docx/.doc）
- 出参：`{ file_id }`

### POST /api/rule/generate
- 入参：`{ file_id }`
- 出参：`{ task_id }`

### GET /api/rule/task/{taskId}
- 规则生成任务状态

### GET /api/rule/my
- 我的格式规则列表（含 pinned 排序、当前 version）

### GET /api/rule/{ruleId}
- 规则详情（最新版本 content）

### GET /api/rule/{ruleId}/version/{version}
- 查看指定版本 content

### GET /api/rule/{ruleId}/export?fmt=json
- 导出规则 JSON 文件（Content-Disposition 附件下载）

### PUT /api/rule/rename
- 入参：`{ rule_id, name }`（≤30 字符，唯一性校验）

### PUT /api/rule/pin
- 入参：`{ rule_id, pinned }`

### DELETE /api/rule/{ruleId}?force=true|false
- 若被格式审查引用且未 force，返回 409

### GET /api/rule/{ruleId}/versions
- 最近 5 个版本

### POST /api/rule/{ruleId}/rollback
- 入参：`{ version }`，回滚后生成新版本号
