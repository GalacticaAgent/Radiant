import axiosInstance from './index'

export interface PaperUploadResponse {
  id: string
  filename: string
  title?: string | null
  file_size: number
  version: number
  created_at: string
}

export interface PaperResponse {
  id: string
  user_id: string
  title?: string | null
  filename: string
  file_size: number
  abstract?: string | null
  paper_metadata?: Record<string, unknown> | null
  version: number
  parent_id?: string | null
  created_at: string
  updated_at?: string | null
}

export interface PaperListResponse {
  papers: PaperResponse[]
  total: number
}

export interface ReviewerRecommendation {
  id: string
  name: string
  affiliation: string
  research_interests: string[]
  h_index: number
  match_count: number
  matched_keywords: string[]
}

export interface ReviewerRecommendationResponse {
  reviewers: ReviewerRecommendation[]
  total: number
}

export interface ReviewerCandidatePaper {
  paper_id?: string | null
  title?: string | null
  abstract?: string | null
  year?: number | null
  venue?: string | null
  citation_count: number
  url?: string | null
}

export interface ReviewerCandidate {
  id: string
  name: string
  affiliation: string
  h_index: number
  citation_count: number
  paper_count: number
  match_score: number
  matched_keywords: string[]
  rationale?: string | null
  source: string
  external_id: string
  top_papers: ReviewerCandidatePaper[]
}

export interface ReviewerCandidateResponse {
  candidates: ReviewerCandidate[]
  total: number
}

export interface CrawlJobResponse {
  id: string
  job_type: string
  target_type: string
  target_id?: string | null
  status: string
  attempts: number
  last_error?: string | null
  created_at: string
  updated_at?: string | null
}

export interface JobStatusResponse {
  status: string
  jobs: CrawlJobResponse[]
}

export interface ReviewResponse {
  id: string
  paper_id: string
  reviewer_id?: string | null
  reviewer_name: string
  reviewer_profile: string
  review_content: string
  rating?: number | null
  confidence?: string | null
  strengths?: string[] | null
  weaknesses?: string[] | null
  suggestions?: string[] | null
  created_at: string
}

export interface ReviewListResponse {
  reviews: ReviewResponse[]
  total: number
}

export interface ModificationSuggestion {
  section: string
  issue: string
  suggestion: string
  priority: string
}

export interface SuggestionsResponse {
  suggestions: ModificationSuggestion[]
  total: number
}

export interface VersionResponse {
  id: string
  version: number
  title?: string | null
  filename: string
  parent_id?: string | null
  created_at: string
}

export interface VersionListResponse {
  versions: VersionResponse[]
  current_version: number
  total: number
}

export interface PaperPolishRequest {
  mode?: 'abstract_only' | 'full'
  selected_suggestions?: string[]
}

export interface PaperPolishResponse {
  paper_id: string
  mode: string
  original_abstract: string
  polished_abstract: string
  diff: string
  applied_suggestions: string[]
  generated_at: string
}

export interface PaperReviewReportResponse {
  paper_id: string
  markdown: string
  generated_at: string
}

export interface FormatIssue {
  severity?: string | null
  position: string
  description: string
  suggestion: string
  evidence?: string | null
}

export interface PaperFormatReviewResponse {
  paper_id: string
  markdown: string
  issues?: FormatIssue[] | null
  rule_issues?: FormatIssue[] | null
  llm_issues?: FormatIssue[] | null
  auto_metrics?: Record<string, any> | null
  overall_grade?: string | null
  priority?: string | null
  generated_at: string
}

export interface AdhocFormatReviewResponse {
  markdown: string
  issues?: FormatIssue[] | null
  rule_issues?: FormatIssue[] | null
  llm_issues?: FormatIssue[] | null
  auto_metrics?: Record<string, any> | null
  overall_grade?: string | null
  priority?: string | null
  generated_at: string
}

export interface SeedDomainExpertsRequest {
  query: string
  per_page?: number
  max_authors?: number
}

export interface SeedDomainExpertsResponse {
  status: string
  task_id?: string | null
}

export const paperAPI = {
  upload: (file: File, title?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    return axiosInstance
      .post<PaperUploadResponse>('/paper/upload', formData, {
        params: title ? { title } : undefined,
        timeout: 120000,
      })
      .then((r) => r.data)
  },
  list: (skip: number = 0, limit: number = 20) =>
    axiosInstance.get<PaperListResponse>('/paper', { params: { skip, limit } }).then((r) => r.data),
  get: (paperId: string) => axiosInstance.get<PaperResponse>(`/paper/${paperId}`).then((r) => r.data),
  reviewers: (paperId: string, limit: number = 5) =>
    axiosInstance
      .get<ReviewerRecommendationResponse>(`/paper/${paperId}/reviewers`, { params: { limit }, timeout: 60000 })
      .then((r) => r.data),
  reviewerCandidates: (paperId: string, limit: number = 5, refresh: boolean = false, signal?: AbortSignal) =>
    axiosInstance
      .get<ReviewerCandidateResponse>(
        `/paper/${paperId}/reviewer-candidates`,
        { params: { limit, refresh }, timeout: 45000, signal }
      )
      .then((r) => r.data),
  reviewerCandidatesStatus: (paperId: string) =>
    axiosInstance.get<JobStatusResponse>(`/paper/${paperId}/reviewer-candidates/status`).then((r) => r.data),
  generateReviews: (paperId: string, reviewerIds: string[]) =>
    axiosInstance
      .post<ReviewListResponse>(`/paper/${paperId}/review`, { reviewer_ids: reviewerIds }, { timeout: 180000 })
      .then((r) => r.data),
  reviews: (paperId: string) =>
    axiosInstance.get<ReviewListResponse>(`/paper/${paperId}/reviews`).then((r) => r.data),
  suggestions: (paperId: string) =>
    axiosInstance.post<SuggestionsResponse>(`/paper/${paperId}/suggestions`, {}, { timeout: 180000 }).then((r) => r.data),
  uploadVersion: (paperId: string, file: File, title?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    return axiosInstance
      .post<PaperUploadResponse>(`/paper/${paperId}/version`, formData, {
        params: title ? { title } : undefined,
        timeout: 120000,
      })
      .then((r) => r.data)
  },
  versions: (paperId: string) =>
    axiosInstance.get<VersionListResponse>(`/paper/${paperId}/versions`).then((r) => r.data),
  polish: (paperId: string, payload: PaperPolishRequest) =>
    axiosInstance.post<PaperPolishResponse>(`/paper/${paperId}/polish`, payload, { timeout: 180000 }).then((r) => r.data),
  report: (paperId: string) =>
    axiosInstance.get<PaperReviewReportResponse>(`/paper/${paperId}/report`).then((r) => r.data),
  formatReview: (paperId: string, scope: 'auto' | 'abstract' | 'full' = 'auto') =>
    axiosInstance.post<PaperFormatReviewResponse>(`/paper/${paperId}/format-review`, { scope }, { timeout: 180000 }).then((r) => r.data),
  formatReviewAdhoc: (formData: FormData) =>
    axiosInstance.post<AdhocFormatReviewResponse>(`/paper/format-review`, formData, { timeout: 180000 }).then((r) => r.data),
  seedDomainExperts: (payload: SeedDomainExpertsRequest) =>
    axiosInstance.post<SeedDomainExpertsResponse>(`/paper/kb/seed-domain-experts`, payload, { timeout: 30000 }).then((r) => r.data),
}
