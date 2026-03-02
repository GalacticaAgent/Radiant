import axiosInstance from './index'

export interface IdeaValidationResult {
  feasibility_score: number
  innovation_score: number
  technical_difficulty: string
  estimated_time: string
  strengths: string[]
  challenges: string[]
  recommendations: string[]
  related_papers: Array<Record<string, unknown>>
  research_directions: string[]
  detailed_analysis: string
}

export const ideaAPI = {
  validate: (idea: string) =>
    axiosInstance.post<IdeaValidationResult>('/idea/validate', { idea }).then((r) => r.data),
}

