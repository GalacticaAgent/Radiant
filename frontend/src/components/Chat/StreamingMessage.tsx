import { useEffect, useState } from 'react'
import { CopyOutlined, ReloadOutlined, CheckOutlined } from '@ant-design/icons'
import { Message } from '../../types/chat'
import { chatStore } from '../../store'
import MarkdownRenderer from '../Common/MarkdownRenderer'
import './StreamingMessage.css'

interface StreamingMessageProps {
  message: Message
  onResend?: (userMessage: string) => void
}

export default function StreamingMessage({ message, onResend }: StreamingMessageProps) {
  const [displayedContent, setDisplayedContent] = useState('')
  const [showCursor, setShowCursor] = useState(true)
  const [copied, setCopied] = useState(false)
  const messages = chatStore((state) => state.messages)

  useEffect(() => {
    if (message.isStreaming) {
      setDisplayedContent(message.content)
    } else {
      // When streaming is done, finalize the content
      setDisplayedContent(message.content)
      setShowCursor(false)
    }
  }, [message.content, message.isStreaming])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(displayedContent)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleRegenerate = () => {
    if (onResend && !message.isStreaming) {
      // Find the previous user message
      const messageIndex = messages.findIndex((m) => m.id === message.id)
      if (messageIndex > 0) {
        for (let i = messageIndex - 1; i >= 0; i--) {
          if (messages[i].role === 'user') {
            onResend(messages[i].content)
            break
          }
        }
      }
    }
  }

  return (
    <div className="message-container ai streaming">
      <div className="message-bubble ai">
        <MarkdownRenderer content={displayedContent} />
        {showCursor && message.isStreaming && (
          <span className="typing-cursor">▊</span>
        )}
      </div>
      <div className="message-footer">
        <span className="message-time">
          {message.isStreaming ? 'typing...' : new Date(message.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
          })}
        </span>
        {!message.isStreaming && (
          <div className="message-actions">
            <button
              className="action-button copy-button"
              onClick={handleCopy}
              title={copied ? 'Copied!' : 'Copy message'}
              aria-label="Copy message"
            >
              {copied ? <CheckOutlined /> : <CopyOutlined />}
            </button>
            <button
              className="action-button regenerate-button"
              onClick={handleRegenerate}
              title="Regenerate response"
              aria-label="Regenerate response"
            >
              <ReloadOutlined />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
