import axiosInstance from './index'

export interface ResearchStartResponse {
  task_id: string
  status: string
  message: string
}

export interface TaskInfo {
  task_id: string
  status: string
  query: string
  created_at: string
  updated_at: string
  progress: number
  message: string
  error?: string | null
}

export interface ResearchResult {
  task_id: string
  query: string
  papers: Array<{
    paper_id: string
    title: string
    authors: string[]
    published_year?: number | null
    venue?: string | null
    url?: string | null
    summary: string
    relevance_score: number
  }>
  total_found: number
  summary: string
  key_trends: string[]
  research_gaps: string[]
  recommendations: string[]
  completed_at: string
}

export const researchAPI = {
  start: (payload: { query: string; sources?: string[]; max_papers?: number; filters?: Record<string, unknown> }) =>
    axiosInstance.post<ResearchStartResponse>('/research/start', payload).then((r) => r.data),
  status: (taskId: string) => axiosInstance.get<TaskInfo>(`/research/status/${taskId}`).then((r) => r.data),
  result: (taskId: string) => axiosInstance.get<ResearchResult>(`/research/result/${taskId}`).then((r) => r.data),
  tasks: () => axiosInstance.get<TaskInfo[]>('/research/tasks').then((r) => r.data),
}
