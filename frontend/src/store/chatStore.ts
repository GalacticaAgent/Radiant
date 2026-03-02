import { create } from 'zustand'
import { Message, Session } from '../types/chat'
import { chatAPI } from '../api/chat'

interface ChatState {
  messages: Message[]
  sessions: Session[]
  currentSessionId: string | null
  isLoading: boolean
  error: string | null
  formatReviewModal: {
    open: boolean
    sessionId: string | null
    paperId: string | null
    paperFilename: string | null
    file: File | null
    text: string | null
    initialActive?: 'review' | 'history' | 'rules' | null
    inserted: boolean
  }
  paperPolishModal: {
    open: boolean
    paperId: string | null
    paperFilename: string | null
    initialTab?: 'reviewers' | 'reviews' | 'suggestions' | 'polish' | 'report' | 'versions' | null
  }
  reviewBoardShortcut: { visible: boolean; paperId: string | null; paperFilename: string | null }
}

interface ChatStoreState extends ChatState {
  addMessage: (message: Message) => void
  updateMessage: (id: string, content: string, isStreaming?: boolean) => void
  setMessages: (messages: Message[]) => void
  setCurrentSessionId: (id: string) => void
  setIsLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  
  // Async actions
  fetchSessions: (signal?: AbortSignal) => Promise<void>
  createNewSession: (title?: string) => Promise<void>
  renameSession: (id: string, title: string) => Promise<void>
  pinSession: (id: string, pinned: boolean) => Promise<void>
  deleteSession: (id: string) => Promise<void>
  loadSession: (id: string) => Promise<void>
  clearHistory: () => void // Keep for compatibility
  openFormatReviewModal: (payload?: {
    sessionId?: string | null
    paperId?: string | null
    paperFilename?: string | null
    file?: File | null
    text?: string | null
    initialActive?: 'review' | 'history' | 'rules' | null
  }) => void
  markFormatReviewInserted: () => void
  closeFormatReviewModal: () => void
  openPaperPolishModal: (payload: {
    paperId: string
    paperFilename?: string | null
    initialTab?: 'reviewers' | 'reviews' | 'suggestions' | 'polish' | 'report' | 'versions' | null
  }) => void
  closePaperPolishModal: () => void
  setReviewBoardShortcut: (payload: { paperId: string; paperFilename?: string | null } | null) => void
}

const CURRENT_SESSION_KEY = 'radiant_current_session'
const LEGACY_MESSAGES_STORAGE_KEY = 'radiant_chat_messages'
const messagesStorageKey = (sessionId: string) => `radiant_chat_messages:${sessionId}`
const reviewShortcutStorageKey = (sessionId: string) => `radiant_review_shortcut:${sessionId}`

export const chatStore = create<ChatStoreState>((set, get) => {
  const savedCurrentSession = localStorage.getItem(CURRENT_SESSION_KEY)

  const initialCurrentSessionId = savedCurrentSession || null
  const sessionCacheRaw = initialCurrentSessionId ? localStorage.getItem(messagesStorageKey(initialCurrentSessionId)) : null
  const legacyRaw = localStorage.getItem(LEGACY_MESSAGES_STORAGE_KEY)
  const initialMessages: Message[] = sessionCacheRaw
    ? JSON.parse(sessionCacheRaw)
    : legacyRaw
      ? JSON.parse(legacyRaw)
      : []
  if (initialCurrentSessionId && legacyRaw && !sessionCacheRaw) {
    localStorage.setItem(messagesStorageKey(initialCurrentSessionId), legacyRaw)
    localStorage.removeItem(LEGACY_MESSAGES_STORAGE_KEY)
  }
  const initialReviewShortcut =
    initialCurrentSessionId && localStorage.getItem(reviewShortcutStorageKey(initialCurrentSessionId))
      ? JSON.parse(localStorage.getItem(reviewShortcutStorageKey(initialCurrentSessionId)) as string)
      : null

  return {
    messages: initialMessages,
    sessions: [],
    currentSessionId: initialCurrentSessionId,
    isLoading: false,
    error: null,
    formatReviewModal: {
      open: false,
      sessionId: null,
      paperId: null,
      paperFilename: null,
      file: null,
      text: null,
      initialActive: null,
      inserted: false,
    },
    paperPolishModal: { open: false, paperId: null, paperFilename: null, initialTab: null },
    reviewBoardShortcut: initialReviewShortcut
      ? { visible: true, paperId: initialReviewShortcut.paperId || null, paperFilename: initialReviewShortcut.paperFilename || null }
      : { visible: false, paperId: null, paperFilename: null },

    addMessage: (message) =>
      set((state) => {
        const newMessages = [...state.messages, message]
        if (state.currentSessionId) {
          localStorage.setItem(messagesStorageKey(state.currentSessionId), JSON.stringify(newMessages))
        }
        return { messages: newMessages }
      }),

    updateMessage: (id, content, isStreaming = false) =>
      set((state) => {
        const newMessages = state.messages.map((msg) =>
          msg.id === id ? { ...msg, content, isStreaming } : msg
        )
        if (state.currentSessionId) {
          localStorage.setItem(messagesStorageKey(state.currentSessionId), JSON.stringify(newMessages))
        }
        return { messages: newMessages }
      }),

    setMessages: (messages) =>
      set((state) => {
        if (state.currentSessionId) {
          localStorage.setItem(messagesStorageKey(state.currentSessionId), JSON.stringify(messages))
        }
        return { messages }
      }),

    setCurrentSessionId: (id) =>
      set(() => {
        localStorage.setItem(CURRENT_SESSION_KEY, id)
        return { currentSessionId: id }
      }),

    setIsLoading: (loading) => set({ isLoading: loading }),

    setError: (error) => set({ error }),

    openFormatReviewModal: (payload) =>
      set((state) => {
        if (state.formatReviewModal.open) return state
        const fallbackSid = get().currentSessionId || (crypto?.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2))
        return {
          formatReviewModal: {
            open: true,
            sessionId: payload?.sessionId || fallbackSid,
            paperId: payload?.paperId || null,
            paperFilename: payload?.paperFilename || null,
            file: payload?.file || null,
            text: payload?.text || null,
            initialActive: payload?.initialActive ?? 'review',
            inserted: false,
          },
        }
      }),

    markFormatReviewInserted: () =>
      set((state) => {
        if (!state.formatReviewModal.open || state.formatReviewModal.inserted) return state
        return {
          formatReviewModal: {
            ...state.formatReviewModal,
            inserted: true,
          },
        }
      }),

    closeFormatReviewModal: () =>
      set(() => ({
        formatReviewModal: {
          open: false,
          sessionId: null,
          paperId: null,
          paperFilename: null,
          file: null,
          text: null,
          initialActive: null,
          inserted: false,
        },
      })),

    openPaperPolishModal: ({ paperId, paperFilename, initialTab }) =>
      set(() => ({ paperPolishModal: { open: true, paperId, paperFilename: paperFilename || null, initialTab: initialTab || null } })),

    closePaperPolishModal: () =>
      set(() => ({ paperPolishModal: { open: false, paperId: null, paperFilename: null, initialTab: null } })),

    setReviewBoardShortcut: (payload) =>
      set(() => {
        const sessionId = get().currentSessionId
        if (!sessionId) return { reviewBoardShortcut: { visible: false, paperId: null, paperFilename: null } }
        if (!payload) {
          localStorage.removeItem(reviewShortcutStorageKey(sessionId))
          return { reviewBoardShortcut: { visible: false, paperId: null, paperFilename: null } }
        }
        localStorage.setItem(
          reviewShortcutStorageKey(sessionId),
          JSON.stringify({ paperId: payload.paperId, paperFilename: payload.paperFilename || null })
        )
        return {
          reviewBoardShortcut: { visible: true, paperId: payload.paperId, paperFilename: payload.paperFilename || null },
        }
      }),

    fetchSessions: async (signal?: AbortSignal) => {
      try {
        const response = await chatAPI.getSessions(signal)
        set({ sessions: response.sessions })
      } catch (error) {
        const err = error as any
        const code = err?.code
        const msg = String(err?.message || '').toLowerCase()
        if (code === 'ERR_CANCELED' || code === 'ERR_ABORTED' || msg.includes('canceled') || msg.includes('aborted')) {
          return
        }
        console.error('Failed to fetch sessions:', error)
        // If API fails (e.g. backend not ready), keep empty or use mock?
        // For now, we assume API works or returns error.
      }
    },

    createNewSession: async () => {
      try {
        const newId = crypto.randomUUID()
        set({ 
          currentSessionId: newId,
          messages: [],
          reviewBoardShortcut: { visible: false, paperId: null, paperFilename: null },
        })
        localStorage.setItem(CURRENT_SESSION_KEY, newId)
        localStorage.setItem(messagesStorageKey(newId), JSON.stringify([]))
        localStorage.removeItem(reviewShortcutStorageKey(newId))
      } catch (error) {
        console.error('Failed to create local session:', error)
      }
    },

    renameSession: async (id, title) => {
      try {
        await chatAPI.renameSession(id, title)
        set((state) => ({
          sessions: state.sessions.map((s) => 
            s.id === id ? { ...s, title } : s
          )
        }))
      } catch (error) {
        console.error('Failed to rename session:', error)
      }
    },

    pinSession: async (id, pinned) => {
      try {
        await chatAPI.pinSession(id, pinned)
        set((state) => ({
          sessions: state.sessions.map((s) => 
            s.id === id ? { ...s, is_pinned: pinned } : s
          )
        }))
        // Re-sort sessions might be needed, but Sidebar can handle it or we re-fetch
        get().fetchSessions() 
      } catch (error) {
        console.error('Failed to pin session:', error)
      }
    },

    deleteSession: async (id) => {
      try {
        await chatAPI.deleteSession(id)
        set((state) => {
          const newSessions = state.sessions.filter((s) => s.id !== id)
          let newCurrentId = state.currentSessionId
          let newMessages = state.messages
          
          if (state.currentSessionId === id) {
             newCurrentId = newSessions[0]?.id || null
             newMessages = newCurrentId ? JSON.parse(localStorage.getItem(messagesStorageKey(newCurrentId)) || '[]') : []
             if (newCurrentId) {
               localStorage.setItem(CURRENT_SESSION_KEY, newCurrentId)
             } else {
               localStorage.removeItem(CURRENT_SESSION_KEY)
             }
          }
          localStorage.removeItem(messagesStorageKey(id))
          localStorage.removeItem(reviewShortcutStorageKey(id))
          
          return { 
            sessions: newSessions,
            currentSessionId: newCurrentId,
            messages: newMessages
          }
        })
      } catch (error) {
        console.error('Failed to delete session:', error)
      }
    },

    loadSession: async (id) => {
      try {
        const cached = JSON.parse(localStorage.getItem(messagesStorageKey(id)) || '[]')
        const shortcutRaw = localStorage.getItem(reviewShortcutStorageKey(id))
        const shortcut = shortcutRaw ? JSON.parse(shortcutRaw) : null
        set({ 
          isLoading: true, 
          currentSessionId: id,
          messages: cached,
          reviewBoardShortcut: shortcut ? { visible: true, paperId: shortcut.paperId || null, paperFilename: shortcut.paperFilename || null } : { visible: false, paperId: null, paperFilename: null },
        })
        localStorage.setItem(CURRENT_SESSION_KEY, id)
        const response = await chatAPI.getHistory(id)
        const messages: Message[] = response.messages
          .filter((m) => m.role === 'user' || m.role === 'assistant')
          .map((m) => ({
            id: crypto.randomUUID(),
            content: m.content,
            role: m.role as 'user' | 'assistant',
            timestamp: m.created_at,
          }))
        localStorage.setItem(messagesStorageKey(id), JSON.stringify(messages))
        set({ messages })
      } catch (error) {
        console.error('Failed to load session:', error)
        // Fallback or error handling
      } finally {
        set({ isLoading: false })
      }
    },
    
    clearHistory: () =>
        set(() => {
          const sessionId = get().currentSessionId
          if (sessionId) localStorage.removeItem(messagesStorageKey(sessionId))
          return { messages: [] }
        }),
  }
})
