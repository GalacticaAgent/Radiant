import axios from 'axios'
import { authStore } from '../store/authStore'

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || '').replace(/\/api\/v1\/?$/, ''),
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  const token = authStore.getState().token
  if (token) {
    config.headers = config.headers || {}
    ;(config.headers as any).Authorization = `Bearer ${token}`
  }
  return config
})

export interface ApiResponse<T> {
  code: number
  msg: string
  data: T
}

export interface UploadInitResult {
  upload_id: string
  chunk_size: number
  expected_parts: number
}

export interface UploadStatusResult {
  upload_id: string
  status: string
  uploaded_parts: number[]
  chunk_size: number
  size: number
  expected_parts: number
  missing_parts: number[]
}

export interface UploadCompleteResult {
  upload_id: string
  status: string
}

export interface FormatReviewStartResult {
  task_id: string
}

export interface FormatReviewTaskResult {
  task_id: string
  session_id: string
  status: string
  progress: number
  result?: any
  error?: string | null
}

export interface FormatReviewHistoryItem {
  history_id: string
  session_id: string
  paper_title?: string | null
  filename?: string | null
  status: string
  duration_ms?: number | null
  issues_count?: number | null
  created_at: string
}

export interface FormatReviewHistoryList {
  total: number
  items: FormatReviewHistoryItem[]
}

export interface FormatReviewAutoFixResult {
  fix_task_id: string
}

export interface FormatReviewFixTaskResult {
  fix_task_id: string
  status: string
  progress: number
  download_url?: string | null
  expires_at?: string | null
  error?: string | null
}

export const formatReviewAPI = {
  initUpload: (payload: { session_id: string; filename: string; size: number; mime_type?: string | null }) =>
    api.post<ApiResponse<UploadInitResult>>(`/api/upload/init`, payload).then((r) => r.data.data),
  uploadPart: (uploadId: string, partNumber: number, chunk: ArrayBuffer) =>
    api.put<ApiResponse<any>>(`/api/upload/${uploadId}/part`, chunk, {
      params: { part_number: partNumber },
      headers: { 'Content-Type': 'application/octet-stream' },
      timeout: 60000,
    }),
  completeUpload: (uploadId: string) =>
    api.post<ApiResponse<UploadCompleteResult>>(`/api/upload/${uploadId}/complete`).then((r) => r.data.data),
  uploadStatus: (uploadId: string) =>
    api.get<ApiResponse<UploadStatusResult>>(`/api/upload/${uploadId}/status`).then((r) => r.data.data),
  start: (payload: { session_id: string; upload_id?: string | null; rule_id?: string | null; paper_title?: string | null; filename?: string | null }) =>
    api.post<ApiResponse<FormatReviewStartResult>>(`/api/format-review/start`, payload).then((r) => r.data.data),
  getTask: (taskId: string) =>
    api.get<ApiResponse<FormatReviewTaskResult>>(`/api/format-review/task/${taskId}`).then((r) => r.data.data),
  saveHistory: (taskId: string) =>
    api.post<ApiResponse<{ history_id: string }>>(`/api/format-review/history/save`, { task_id: taskId }).then((r) => r.data.data),
  listHistory: (sessionId: string, page: number = 1, pageSize: number = 10, q?: string) =>
    api
      .get<ApiResponse<FormatReviewHistoryList>>(`/api/format-review/history`, { params: { session_id: sessionId, page, page_size: pageSize, q } })
      .then((r) => r.data.data),
  deleteHistory: (historyId: string) => api.delete<ApiResponse<any>>(`/api/format-review/history/${historyId}`),
  autoFix: (historyId: string) =>
    api.post<ApiResponse<FormatReviewAutoFixResult>>(`/api/format-review/auto-fix`, { history_id: historyId }).then((r) => r.data.data),
  getFixTask: (fixTaskId: string) =>
    api.get<ApiResponse<FormatReviewFixTaskResult>>(`/api/format-review/auto-fix/${fixTaskId}`).then((r) => r.data.data),
}
