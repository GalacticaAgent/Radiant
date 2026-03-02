import { AppLayout } from '../../components/Layout'
import { ChatBox } from '../../components/Chat'
import './PaperPolish.css'

export default function PaperPolish() {
  return (
    <AppLayout>
      <div className="polish-page" style={{ height: '100%', padding: 0 }}>
        <ChatBox />
      </div>
    </AppLayout>
  )
}
