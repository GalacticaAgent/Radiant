import { AppLayout } from '../../components/Layout'
import { ChatBox } from '../../components/Chat'
import './Home.css'

export default function Home() {
  return (
    <AppLayout>
      <div className="home-page">
        <ChatBox />
      </div>
    </AppLayout>
  )
}
