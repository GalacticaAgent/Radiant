import { useEffect, useState, useRef } from 'react'
import { Message } from '../../types/chat'
import './ChatNavigator.css'

interface ChatNavigatorProps {
  messages: Message[]
  onNavigate?: (messageId: string) => void
  currentVisibleMessageId?: string
}

export default function ChatNavigator({ messages, onNavigate, currentVisibleMessageId }: ChatNavigatorProps) {
  const [visibleMessageId, setVisibleMessageId] = useState<string | null>(currentVisibleMessageId || null)
  const navigationRef = useRef<HTMLDivElement>(null)

  // Extract topic/summary from message content
  const getMessageSummary = (message: Message): string => {
    const content = message.content
    if (content.length === 0) {
      return message.role === 'user' ? 'User...' : 'AI...'
    }

    // Get first 40 characters, truncate if needed
    let summary = content.substring(0, 40).trim()
    if (content.length > 40) {
      summary += '...'
    }

    // Replace newlines with spaces
    summary = summary.replace(/\n/g, ' ')

    return summary
  }

  const handleNavigate = (messageId: string) => {
    setVisibleMessageId(messageId)
    if (onNavigate) {
      onNavigate(messageId)
    }

    // Scroll the navigator item into view
    const item = navigationRef.current?.querySelector(
      `[data-message-id="${messageId}"]`
    ) as HTMLElement
    if (item) {
      item.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }

  // Update visible message when prop changes
  useEffect(() => {
    if (currentVisibleMessageId) {
      setVisibleMessageId(currentVisibleMessageId)
    }
  }, [currentVisibleMessageId])

  if (messages.length === 0) {
    return null
  }

  return (
    <div className="chat-navigator">
      <div className="navigator-header">
        <span className="navigator-title">Messages</span>
        <span className="message-count">{messages.length}</span>
      </div>
      <div className="navigator-list" ref={navigationRef}>
        {messages.map((message, index) => (
          <button
            key={message.id}
            className={`navigator-item ${message.role === 'user' ? 'user' : 'ai'} ${
              visibleMessageId === message.id ? 'active' : ''
            }`}
            onClick={() => handleNavigate(message.id)}
            title={message.content}
            data-message-id={message.id}
          >
            <span className="navigator-index">{index + 1}</span>
            <span className="navigator-summary">{getMessageSummary(message)}</span>
            <span className="navigator-role-badge">{message.role === 'user' ? 'U' : 'A'}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
