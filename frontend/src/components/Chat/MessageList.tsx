import { useEffect, useRef } from 'react'
import { Message } from '../../types/chat'
import MessageItem from './MessageItem'
import StreamingMessage from './StreamingMessage'
import './MessageList.css'

interface MessageListProps {
  messages: Message[]
  onResend?: (message: string) => void
}

export default function MessageList({ messages, onResend }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const shouldAutoScrollRef = useRef(true)

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    if (messagesEndRef.current && shouldAutoScrollRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Detect if user has scrolled up manually
  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100
      shouldAutoScrollRef.current = isNearBottom
    }
  }

  if (messages.length === 0) {
    return (
      <div className="message-list-empty">
        <div className="empty-state">
          <h2>Welcome to Radiant</h2>
          <p>Your AI-powered academic research assistant</p>
          <p>Start a conversation to begin exploring research topics</p>
        </div>
      </div>
    )
  }

  return (
    <div className="message-list" ref={containerRef} onScroll={handleScroll}>
      <div className="messages-container">
        {messages.map((message) =>
          message.isStreaming ? (
            <StreamingMessage key={message.id} message={message} onResend={onResend} />
          ) : (
            <MessageItem key={message.id} message={message} onResend={onResend} />
          )
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}
