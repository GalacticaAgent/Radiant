import { useRef, useCallback, useState, useEffect } from 'react'
import { chatAPI } from '../api/chat'
import { chatStore } from '../store'
import { Message } from '../types/chat'

interface UseStreamingChatReturn {
  sendMessage: (content: string, files?: File[]) => Promise<void>
  isLoading: boolean
  error: string | null
  cancelStream: () => void
}

const generateId = (): string => Math.random().toString(36).substr(2, 9)

export const useStreamingChat = (): UseStreamingChatReturn => {
  const eventSourceRef = useRef<EventSource | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const currentSessionId = chatStore((state) => state.currentSessionId)
  const addMessage = chatStore((state) => state.addMessage)
  const updateMessage = chatStore((state) => state.updateMessage)
  const fetchSessions = chatStore((state) => state.fetchSessions)

  // Clean up EventSource on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  const cancelStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsLoading(false)
  }, [])

  const sendMessage = useCallback(
    async (content: string, files?: File[]): Promise<void> => {
      if (!content.trim() && (!files || files.length === 0)) {
        setError('Message cannot be empty')
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const primaryFile = files?.[0]
        const finalUserContent = (!content.trim() && primaryFile)
          ? '请基于我上传的附件内容回答。'
          : content

        // Add user message
        const userMessageId = generateId()
        
        const attachments = files?.map(f => ({
            name: f.name,
            type: f.type,
            size: f.size,
            url: URL.createObjectURL(f) // Mock URL for preview
        }))

        const userMessage: Message = {
          id: userMessageId,
          content: finalUserContent,
          role: 'user',
          timestamp: new Date().toISOString(),
          attachments
        }
        addMessage(userMessage)

        // Create AI message placeholder
        const aiMessageId = generateId()
        const aiMessage: Message = {
          id: aiMessageId,
          content: '',
          role: 'assistant',
          timestamp: new Date().toISOString(),
          isStreaming: true,
        }
        addMessage(aiMessage)

        if (primaryFile) {
          const res = await chatAPI.sendMessageWithFile({
            message: finalUserContent,
            session_id: currentSessionId || undefined,
            search_graph: true,
            file: primaryFile,
          })
          updateMessage(aiMessageId, res.content || '', false)
          setIsLoading(false)
          fetchSessions()
          return
        }

        // Connect to SSE stream
        // Note: files are not sent to backend yet as SSE get request doesn't support body/files easily.
        // We'd need a separate POST endpoint for files + message -> SSE.
        // For now, we only stream text.
        try {
          await chatAPI.getSessions()
        } catch {
        }
        const streamUrl = chatAPI.getStreamUrl(finalUserContent, currentSessionId || undefined)
        const eventSource = new EventSource(streamUrl)
        eventSourceRef.current = eventSource

        let fullContent = ''

        eventSource.onmessage = (event) => {
          try {
            // 尝试解析 JSON 格式（推荐格式：{"content": "...", "done": true/false}）
            const data = JSON.parse(event.data)
            fullContent += data.content || ''
            updateMessage(aiMessageId, fullContent, !data.done)

            if (data.done) {
              eventSource.close()
              eventSourceRef.current = null
              setIsLoading(false)
              fetchSessions() // Update sidebar with new session if needed
            }
          } catch (e) {
            // 如果不是 JSON，则当作纯文本处理（兼容模式）
            // 后端直接发送文本块时会进入此分支
            fullContent += event.data
            updateMessage(aiMessageId, fullContent, true)
          }
        }

        eventSource.onerror = async () => {
          console.error('SSE connection error or stream completed')
          eventSource.close()
          eventSourceRef.current = null

          // Check if it's an auth error (401) by making a quick API call
          // SSE doesn't expose status codes, so we infer from a failed API call
          try {
            await chatAPI.getSessions()
          } catch (e) {
            // If 401, axios interceptor will handle logout/refresh
            console.error('Connection check failed:', e)
          }

          // Finalize the message (set isStreaming to false)
          if (fullContent) {
            updateMessage(aiMessageId, fullContent, false)
          } else {
            // Only show error if we didn't receive any content
            setError('Connection failed. Please check your network or try logging in again.')
          }
          setIsLoading(false)
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred'
        setError(errorMessage)
        setIsLoading(false)
      }
    },
    [currentSessionId, addMessage, updateMessage]
  )

  return {
    sendMessage,
    isLoading,
    error,
    cancelStream,
  }
}
