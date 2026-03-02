import axiosInstance from './index'

export interface GraphSearchResponse {
  results: Array<Record<string, unknown>>
  total: number
}

export interface SubgraphResponse {
  nodes: Array<Record<string, unknown>>
  edges: Array<Record<string, unknown>>
}

export const graphAPI = {
  search: (q: string, type?: string, limit: number = 20) =>
    axiosInstance
      .get<GraphSearchResponse>('/graph/search', { params: { q, type, limit } })
      .then((r) => r.data),
  subgraph: (query: string, depth: number = 2, limit: number = 100, node_type?: string) =>
    axiosInstance
      .get<SubgraphResponse>('/graph/subgraph', { params: { query, depth, limit, node_type } })
      .then((r) => r.data),
}

