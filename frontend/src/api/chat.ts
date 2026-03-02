import axiosInstance from './index'
import { Session, ChatRequest, ChatResponse, ConversationHistoryResponse } from '../types/chat'
import { authStore } from '../store/authStore'

export const chatAPI = {
  // Send a message and get a response
  sendMessage: (data: ChatRequest): Promise<ChatResponse> =>
    axiosInstance.post('/chat/send', data).then((res) => res.data),

  sendMessageWithFile: (payload: {
    message: string
    session_id?: string
    search_graph?: boolean
    file: File
  }): Promise<ChatResponse> => {
    const formData = new FormData()
    formData.append('message', payload.message)
    if (payload.session_id) formData.append('session_id', payload.session_id)
    formData.append('search_graph', String(payload.search_graph ?? true))
    formData.append('file', payload.file)
    return axiosInstance.post('/chat/send-file', formData, { timeout: 180000 }).then((res) => res.data)
  },

  // Get chat history
  getHistory: (sessionId: string): Promise<ConversationHistoryResponse> =>
    axiosInstance.get(`/chat/history?session_id=${sessionId}`).then((res) => res.data),

  // Delete a session
  deleteSession: (sessionId: string): Promise<void> =>
    axiosInstance.delete(`/chat/session/${sessionId}`).then((res) => res.data),

  // Rename a session
  renameSession: (sessionId: string, title: string): Promise<Session> =>
    axiosInstance.put(`/chat/session/${sessionId}`, { title }).then((res) => res.data),

  // Pin a session
  pinSession: (sessionId: string, pinned: boolean): Promise<Session> =>
    axiosInstance.put(`/chat/session/${sessionId}/pin`, { pinned }).then((res) => res.data),

  // Get all sessions
  getSessions: (signal?: AbortSignal): Promise<{ sessions: Session[] }> =>
    axiosInstance.get('/chat/sessions', signal ? { signal } : undefined).then((res) => res.data),

  // Clear session history
  clearSession: (sessionId: string): Promise<void> =>
    axiosInstance.post(`/chat/clear?session_id=${sessionId}`).then((res) => res.data),

  // Append a message to a session without triggering LLM
  appendMessage: (data: { session_id: string; role: 'user' | 'assistant' | 'system'; content: string; references?: any }): Promise<{ session_id: string; created_at: string }> =>
    axiosInstance.post('/chat/append', data).then((res) => res.data),

  // Stream chat (returns EventSource URL)
  getStreamUrl: (message: string, sessionId?: string): string => {
    const params = new URLSearchParams()
    params.append('message', message)
    if (sessionId) {
      params.append('session_id', sessionId)
    }

    // Add token to query parameters since EventSource doesn't support custom headers
    const token = authStore.getState().token
    if (token) {
      params.append('token', token)
    }

    const baseUrl = axiosInstance.defaults.baseURL || ''
    return `${baseUrl}/chat/stream?${params.toString()}`
  },
}
