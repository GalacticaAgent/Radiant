export interface Attachment {
  name: string
  url?: string
  type: string
  size?: number
}

export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  isStreaming?: boolean
  attachments?: Attachment[]
}

export interface Session {
  id: string
  title: string
  is_pinned: boolean
  created_at: string
  updated_at: string
}

export interface ChatRequest {
  message: string
  session_id?: string
}

export interface ChatResponse {
  message_id: string
  content: string
  references?: Array<{
    type: string
    id: string
    title: string
    url?: string
  }>
  session_id: string
}

export interface StreamChatResponse {
  content: string
  done: boolean
}

export interface ConversationMessage {
  role: string
  content: string
  references?: Record<string, unknown> | null
  created_at: string
}

export interface ConversationHistoryResponse {
  session_id: string
  messages: ConversationMessage[]
  total: number
}
