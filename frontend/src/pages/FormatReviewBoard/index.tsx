import { AppLayout } from '../../components/Layout'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { useEffect, useMemo } from 'react'
import FormatReviewBoardCore from '../../components/FormatReviewBoardCore'
import './index.css'

type LocationState = {
  sessionId?: string
  paperId?: string | null
  paperFilename?: string | null
  file?: File | null
  text?: string | null
}

export default function FormatReviewBoard() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const state = (location.state || {}) as LocationState

  const sid = useMemo(() => sessionId || state.sessionId || (crypto?.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2)), [sessionId])

  useEffect(() => {
    if (!sessionId) {
      navigate(`/format-review/${sid}`, { replace: true })
    }
  }, [sessionId, sid])

  return (
    <AppLayout>
      <FormatReviewBoardCore
        sessionId={sid}
        incoming={{
          paperId: state.paperId ?? null,
          paperFilename: state.paperFilename ?? null,
          file: state.file ?? null,
          text: state.text ?? null,
        }}
      />
    </AppLayout>
  )
}

