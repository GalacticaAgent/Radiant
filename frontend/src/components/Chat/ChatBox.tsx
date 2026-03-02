import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { App } from 'antd'
import { chatStore } from '../../store'
import { useStreamingChat } from '../../hooks/useStreamingChat'
import MessageList from './MessageList'
import InputBox from './InputBox'
import { BulbOutlined, SearchOutlined, FileTextOutlined } from '@ant-design/icons'
import { paperAPI } from '../../api/paper'
import { chatAPI } from '../../api/chat'
import PaperPolishModal from '../PaperPolishModal'
import FormatReviewModal from '../FormatReviewModal'
import './ChatBox.css'

export default function ChatBox() {
  const { message } = App.useApp()
  const { id } = useParams<{ id: string }>()
  const messages = chatStore((state) => state.messages)
  const loadSession = chatStore((state) => state.loadSession)
  const currentSessionId = chatStore((state) => state.currentSessionId)
  const createNewSession = chatStore((state) => state.createNewSession)
  const addMessage = chatStore((state) => state.addMessage)
  const { sendMessage, isLoading, error, cancelStream } = useStreamingChat()
  const genId = () => (crypto?.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2))
  const paperPolishModal = chatStore((state) => state.paperPolishModal)
  const openPaperPolishModal = chatStore((state) => state.openPaperPolishModal)
  const closePaperPolishModal = chatStore((state) => state.closePaperPolishModal)
  const formatReviewModal = chatStore((state) => state.formatReviewModal)
  const openFormatReviewModal = chatStore((state) => state.openFormatReviewModal)
  const closeFormatReviewModal = chatStore((state) => state.closeFormatReviewModal)
  const reviewBoardShortcut = chatStore((state) => state.reviewBoardShortcut)
  const setReviewBoardShortcut = chatStore((state) => state.setReviewBoardShortcut)

  const persistMessage = (role: 'user' | 'assistant' | 'system', content: string) => {
    const sid = chatStore.getState().currentSessionId
    if (!sid || !content) return
    chatAPI.appendMessage({ session_id: sid, role, content }).catch(() => {})
  }

  useEffect(() => {
    if (id && id !== currentSessionId) {
      loadSession(id)
    } else if (!id && !currentSessionId) {
        // Initial load on home page without ID -> create new session state
        createNewSession()
    }
  }, [id, loadSession, currentSessionId, createNewSession])

  const handleSend = async (content: string, files?: File[], options?: { simulatedReview?: boolean }) => {
    const selectedFile = files?.[0]
    if (options?.simulatedReview && selectedFile) {
      const lower = selectedFile.name.toLowerCase()
      const ok = lower.endsWith('.pdf') || lower.endsWith('.docx') || lower.endsWith('.doc')
      if (!ok) {
        message.error('模拟审稿仅支持上传 PDF/DOCX/DOC 论文')
        return
      }

      const userText = content.trim() || '请对这篇论文进行模拟审稿'
      const userMessageId = genId()
      addMessage({
        id: userMessageId,
        content: userText,
        role: 'user',
        timestamp: new Date().toISOString(),
        attachments: [{ name: selectedFile.name, type: selectedFile.type, size: selectedFile.size }],
      })
      persistMessage('user', userText)

      const loadingKey = 'paper-upload'
      message.loading({ content: '正在上传论文...', key: loadingKey, duration: 0 })
      try {
        const uploaded = await paperAPI.upload(selectedFile)
        message.success({ content: '论文已上传，进入模拟审稿流程', key: loadingKey, duration: 2 })
        setReviewBoardShortcut({ paperId: uploaded.id, paperFilename: selectedFile.name })

        addMessage({
          id: genId(),
          content: `已收到论文 **${selectedFile.name}**。\n\n请在弹窗中选择审稿人并开始审稿。`,
          role: 'assistant',
          timestamp: new Date().toISOString(),
        })
        persistMessage('assistant', `已收到论文 **${selectedFile.name}**。\n\n请在弹窗中选择审稿人并开始审稿。`)

        openPaperPolishModal?.({ paperId: uploaded.id, paperFilename: selectedFile.name })
      } catch (e: any) {
        message.error({ content: e?.message || e?.response?.data?.detail || '论文上传失败', key: loadingKey, duration: 3 })
      }
      return
    }

    await sendMessage(content, files)
  }

  const handleCancel = () => {
    cancelStream()
  }

  const handleResend = async (userMessage: string) => {
    await sendMessage(userMessage)
  }

  const handleQuickPrompt = (prompt: string) => {
    sendMessage(prompt)
  }

  return (
    <div className="chat-box">
      {error && (
        <div className="chat-error">
          <p>{error}</p>
        </div>
      )}
      
      {messages.length === 0 ? (
        <div className="welcome-screen">
          <div className="welcome-content">
            <h1>What can I help you with?</h1>
            <p className="subtitle">Your AI-powered academic research assistant</p>
            
            <div className="quick-prompts">
              <button className="prompt-card" onClick={() => handleQuickPrompt('Find latest papers on Large Language Models')}>
                <SearchOutlined className="prompt-icon" />
                <div className="prompt-text">
                  <span className="prompt-title">Literature Search</span>
                  <span className="prompt-desc">Find latest papers on LLMs</span>
                </div>
              </button>
              
              <button className="prompt-card" onClick={() => handleQuickPrompt('Validate my research idea: Using RLHF for code generation')}>
                <BulbOutlined className="prompt-icon" />
                <div className="prompt-text">
                  <span className="prompt-title">Idea Validation</span>
                  <span className="prompt-desc">Validate research idea</span>
                </div>
              </button>
              
              <button className="prompt-card" onClick={() => handleQuickPrompt('Help me polish this abstract...')}>
                <FileTextOutlined className="prompt-icon" />
                <div className="prompt-text">
                  <span className="prompt-title">Paper Polish</span>
                  <span className="prompt-desc">Improve academic writing</span>
                </div>
              </button>
            </div>
          </div>
        </div>
      ) : (
        <MessageList messages={messages} onResend={handleResend} />
      )}
      
      <InputBox
        onSend={handleSend}
        onCancel={handleCancel}
        isLoading={isLoading}
        reviewBoardVisible={!!paperPolishModal?.open || !!reviewBoardShortcut?.paperId}
        onOpenFormatReview={async ({ text, files }) => {
          const file = files?.[0]
          const trimmed = (text || '').trim()
          const paperId = reviewBoardShortcut?.paperId || null
          const paperFilename = reviewBoardShortcut?.paperFilename || null
          const current = chatStore.getState().currentSessionId
          if (!current) {
            await createNewSession()
          }
          const sid = chatStore.getState().currentSessionId
          openFormatReviewModal?.({
            sessionId: sid,
            paperId,
            paperFilename,
            file: (file as any) || null,
            text: trimmed || null,
            initialActive: 'review',
          })
        }}
        onOpenReviewBoard={() => {
          if (reviewBoardShortcut?.paperId) {
            openPaperPolishModal?.({ paperId: reviewBoardShortcut.paperId, paperFilename: reviewBoardShortcut.paperFilename })
            return
          }
          message.info('请先上传论文（PDF）进入模拟审稿流程')
        }}
      />

      <PaperPolishModal
        open={!!paperPolishModal?.open}
        paperId={paperPolishModal?.paperId || null}
        paperFilename={paperPolishModal?.paperFilename || null}
        initialTab={paperPolishModal?.initialTab || null}
        onClose={() => closePaperPolishModal?.()}
        onAppendToChat={(content) => {
          addMessage({
            id: genId(),
            content,
            role: 'assistant',
            timestamp: new Date().toISOString(),
          })
          persistMessage('assistant', content)
        }}
        onReviewsGenerated={(reviews, meta) => {
          setReviewBoardShortcut({ paperId: meta.paperId, paperFilename: paperPolishModal?.paperFilename || null })
          const title = `# 模拟审稿结果\n\n- Paper ID: ${meta.paperId}\n- Reviewers: ${meta.reviewerIds.join(', ')}\n\n`
          addMessage({
            id: genId(),
            content: title,
            role: 'assistant',
            timestamp: new Date().toISOString(),
          })
          persistMessage('assistant', title)

          reviews.forEach((r, idx) => {
            const hasSections = /(优点|缺点|建议|Strengths|Weaknesses|Suggestions)/i.test(r.review_content || '')
            const hasRating = /(评分|Rating)/i.test(r.review_content || '')
            const parts: string[] = []
            parts.push(`## Reviewer ${idx + 1}: ${r.reviewer_name || r.reviewer_id || 'Unknown'}`)
            if (!hasRating && r.rating !== null && r.rating !== undefined) parts.push(`- Rating: ${r.rating}/10`)
            parts.push('')
            if (r.review_content) parts.push(r.review_content.trim())
            if (!hasSections && r.strengths?.length) {
              parts.push('')
              parts.push('**Strengths**')
              parts.push('')
              parts.push(r.strengths.map((x) => `- ${x}`).join('\n'))
            }
            if (!hasSections && r.weaknesses?.length) {
              parts.push('')
              parts.push('**Weaknesses**')
              parts.push('')
              parts.push(r.weaknesses.map((x) => `- ${x}`).join('\n'))
            }
            if (!hasSections && r.suggestions?.length) {
              parts.push('')
              parts.push('**Suggestions**')
              parts.push('')
              parts.push(r.suggestions.map((x) => `- ${x}`).join('\n'))
            }
            addMessage({
              id: genId(),
              content: parts.join('\n').trim() + '\n',
              role: 'assistant',
              timestamp: new Date().toISOString(),
            })
            persistMessage('assistant', parts.join('\n').trim() + '\n')
          })
        }}
      />

      <FormatReviewModal
        open={!!formatReviewModal?.open}
        sessionId={formatReviewModal?.sessionId || null}
        paperId={formatReviewModal?.paperId || null}
        paperFilename={formatReviewModal?.paperFilename || null}
        file={formatReviewModal?.file || null}
        text={formatReviewModal?.text || null}
        initialActive={formatReviewModal?.initialActive ?? 'review'}
        onAppendToChat={(content) => {
          addMessage({
            id: genId(),
            content,
            role: 'assistant',
            timestamp: new Date().toISOString(),
          })
          persistMessage('assistant', content)
        }}
        onClose={() => closeFormatReviewModal?.()}
      />
    </div>
  )
}
