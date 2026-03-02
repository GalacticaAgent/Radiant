import { useState } from 'react'
import { CopyOutlined, ReloadOutlined, CheckOutlined, FileOutlined } from '@ant-design/icons'
import { Message } from '../../types/chat'
import { chatStore } from '../../store'
import MarkdownRenderer from '../Common/MarkdownRenderer'
import './MessageItem.css'

interface MessageItemProps {
  message: Message
  onResend?: (userMessage: string) => void
}

export default function MessageItem({ message, onResend }: MessageItemProps) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'
  const messages = chatStore((state) => state.messages)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleRegenerate = () => {
    if (!isUser && onResend) {
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
    <div className={isUser ? 'message-container user' : 'message-container ai'}>
      <div className={isUser ? 'message-bubble user' : 'message-bubble ai'}>
        {message.attachments && message.attachments.length > 0 && (
           <div className="message-attachments">
              {message.attachments.map((file, idx) => (
                  <div key={idx} className="attachment-item">
                     <FileOutlined />
                     <span className="attachment-name">{file.name}</span>
                  </div>
              ))}
           </div>
        )}
        {isUser ? (
          <p className="message-content">{message.content}</p>
        ) : (
          <MarkdownRenderer content={message.content} />
        )}
      </div>
      <div className="message-footer">
        {!isUser && (
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
