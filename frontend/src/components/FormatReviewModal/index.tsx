import { Modal } from 'antd'
import FormatReviewBoardCore from '../FormatReviewBoardCore'

type Props = {
  open: boolean
  sessionId: string | null
  paperId: string | null
  paperFilename: string | null
  file: File | null
  text: string | null
  initialActive?: 'review' | 'history' | 'rules' | null
  onAppendToChat?: (content: string) => void
  onClose: () => void
}

export default function FormatReviewModal({ open, sessionId, paperId, paperFilename, file, text, initialActive, onAppendToChat, onClose }: Props) {
  if (!sessionId) return null

  return (
    <Modal
      open={open}
      title="格式审查"
      width={1200}
      onCancel={onClose}
      footer={null}
      destroyOnHidden
      maskClosable={false}
    >
      <FormatReviewBoardCore
        sessionId={sessionId}
        incoming={{ paperId, paperFilename, file, text }}
        initialActive={initialActive ?? 'review'}
        onAppendToChat={onAppendToChat}
      />
    </Modal>
  )
}
