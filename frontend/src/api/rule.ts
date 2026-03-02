import axios from 'axios'
import { authStore } from '../store/authStore'

export interface ApiResponse<T> {
  code: number
  msg: string
  data: T
}

export interface RuleItem {
  rule_id: string
  name: string
  pinned: boolean
  version: number
  created_at: string
}

export interface RuleDetail {
  rule_id: string
  name: string
  pinned: boolean
  version: number
  content: any
  created_at: string
  updated_at: string
}

export interface RuleVersionItem {
  version: number
  created_at: string
}

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

export const ruleAPI = {
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<ApiResponse<{ file_id: string }>>('/api/rule/upload', form).then((r) => r.data.data)
  },
  generate: (fileId: string) =>
    api.post<ApiResponse<{ task_id: string }>>('/api/rule/generate', { file_id: fileId }).then((r) => r.data.data),
  task: (taskId: string, options?: { signal?: AbortSignal }) =>
    api
      .get<ApiResponse<{ task_id: string; status: string; rule_id?: string; error?: string }>>(`/api/rule/task/${taskId}`, {
        signal: options?.signal,
      })
      .then((r) => r.data.data),
  my: () => api.get<ApiResponse<{ items: RuleItem[] }>>('/api/rule/my').then((r) => r.data.data),
  detail: (ruleId: string) => api.get<ApiResponse<RuleDetail>>(`/api/rule/${ruleId}`).then((r) => r.data.data),
  versions: (ruleId: string) => api.get<ApiResponse<{ rule_id: string; versions: RuleVersionItem[] }>>(`/api/rule/${ruleId}/versions`).then((r) => r.data.data),
  version: (ruleId: string, version: number) => api.get<ApiResponse<{ rule_id: string; name: string; version: number; content: any; created_at: string }>>(`/api/rule/${ruleId}/version/${version}`).then((r) => r.data.data),
  rollback: (ruleId: string, version: number) =>
    api.post<ApiResponse<{ rule_id: string; version: number }>>(`/api/rule/${ruleId}/rollback`, { version }).then((r) => r.data.data),
  rename: (ruleId: string, name: string) => api.put<ApiResponse<any>>('/api/rule/rename', { rule_id: ruleId, name }),
  renameSkill: (ruleId: string, skillName: string) => api.put<ApiResponse<any>>('/api/rule/skill/rename', { rule_id: ruleId, skill_name: skillName }),
  pin: (ruleId: string, pinned: boolean) => api.put<ApiResponse<any>>('/api/rule/pin', { rule_id: ruleId, pinned }),
  remove: (ruleId: string, force: boolean = false) => api.delete<ApiResponse<any>>(`/api/rule/${ruleId}`, { params: { force } }),
  exportUrl: (ruleId: string) => `${(import.meta.env.VITE_API_BASE_URL || '').replace(/\/api\/v1\/?$/, '')}/api/rule/${ruleId}/export?fmt=json`,
  exportSkillUrl: (ruleId: string) => `${(import.meta.env.VITE_API_BASE_URL || '').replace(/\/api\/v1\/?$/, '')}/api/rule/${ruleId}/export?fmt=skill_md`,
}
