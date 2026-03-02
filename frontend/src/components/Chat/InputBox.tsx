import { useRef, useEffect, useState } from 'react'
import { ArrowUpOutlined, StopOutlined, DeploymentUnitOutlined, GlobalOutlined, PaperClipOutlined, CloseOutlined, FileOutlined } from '@ant-design/icons'
import './InputBox.css'

interface InputBoxProps {
  onSend: (message: string, files?: File[], options?: { simulatedReview?: boolean }) => void
  onCancel?: () => void
  disabled?: boolean
  isLoading?: boolean
  reviewBoardVisible?: boolean
  onOpenReviewBoard?: () => void
  onOpenFormatReview?: (payload: { text: string; files: File[] }) => void
}

export default function InputBox({
  onSend,
  onCancel,
  disabled = false,
  isLoading = false,
  reviewBoardVisible = false,
  onOpenReviewBoard,
  onOpenFormatReview,
}: InputBoxProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [message, setMessage] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [isSimulatedReview, setIsSimulatedReview] = useState(false)

  // Auto-expand textarea
  const adjustHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      const newHeight = Math.min(textareaRef.current.scrollHeight, 150)
      textareaRef.current.style.height = newHeight + 'px'
    }
  }

  // Effect is still useful for initial adjustment, but CSS resize:vertical will handle manual
  useEffect(() => {
    adjustHeight()
  }, [message])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter to send, Shift+Enter for new line
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
    // Shift+Enter allows natural newline behavior (default)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.currentTarget.files || [])
    if (selected.length > 0) {
      setFiles(selected.slice(0, 1))
    }
    // clear input value to allow re-selecting same file
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleSend = () => {
    const trimmed = message.trim()
    if (!trimmed && files.length > 0 && !isSimulatedReview) {
      return
    }
    if ((trimmed || files.length > 0) && !isLoading && !disabled) {
      onSend(trimmed, files, { simulatedReview: isSimulatedReview })
      setMessage('')
      setFiles([])
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleCancel = () => {
    if (onCancel) {
      onCancel()
    }
  }

  return (
    <div className="input-box">
      <div className="input-wrapper">
        {files.length > 0 && (
          <div className="file-preview-area">
            {files.map((file, index) => (
              <div key={index} className="file-preview-item">
                <FileOutlined className="file-icon" />
                <span className="file-name">{file.name}</span>
                <button type="button" className="remove-file-btn" onClick={() => removeFile(index)}>
                  <CloseOutlined />
                </button>
              </div>
            ))}
          </div>
        )}
        <textarea
          ref={textareaRef}
          className="input-textarea"
          placeholder="给 Radiant 发送消息"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          rows={1}
        />
        
        <div className="input-toolbar">
          <div className="toolbar-left">
            <button 
              className="feature-toggle deep-think active"
              onClick={() => onOpenFormatReview?.({ text: message.trim(), files })}
              title="打开格式审查"
              type="button"
            >
              <DeploymentUnitOutlined />
              <span>格式审查</span>
            </button>
            
            <button 
              className={`feature-toggle web-search ${isSimulatedReview ? 'active' : ''}`}
              onClick={() => setIsSimulatedReview(!isSimulatedReview)}
              title={isSimulatedReview ? "模拟审稿已开启" : "开启模拟审稿"}
              type="button"
            >
              <GlobalOutlined />
              <span>模拟审稿</span>
            </button>

            <button
              className={`feature-toggle web-search ${reviewBoardVisible ? 'active' : ''}`}
              onClick={() => onOpenReviewBoard?.()}
              title={reviewBoardVisible ? '返回审稿看板' : '打开审稿看板'}
              type="button"
            >
              <GlobalOutlined />
              <span>审稿看板</span>
            </button>
          </div>
          
          <div className="toolbar-right">
            <input 
                type="file" 
                ref={fileInputRef} 
                style={{ display: 'none' }} 
                accept=".pdf,.docx,.doc,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={handleFileSelect}
            />
            <button 
                className="attach-button" 
                title="Attach file"
                onClick={() => fileInputRef.current?.click()}
                type="button"
            >
              <PaperClipOutlined />
            </button>
            
            {isLoading ? (
              <button
                className="action-button stop-button"
                onClick={handleCancel}
                title="Stop generating"
                type="button"
              >
                <StopOutlined />
              </button>
            ) : (
              <button
                className="action-button send-button"
                onClick={handleSend}
                disabled={
                  (!message.trim() && files.length === 0) ||
                  (!message.trim() && files.length > 0 && !isSimulatedReview) ||
                  isLoading ||
                  disabled
                }
                title="Send message"
                type="button"
              >
                <ArrowUpOutlined />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
