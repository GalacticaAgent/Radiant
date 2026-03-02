import { MenuOutlined, MenuUnfoldOutlined, PlusOutlined } from '@ant-design/icons'
import { Button } from 'antd'
import { useNavigate } from 'react-router-dom'
import { uiStore, chatStore } from '../../store'
import styles from '../../styles/layout.module.css'
import './Header.css'

export default function Header() {
  const toggleSidebar = uiStore((state) => state.toggleSidebar)
  const sidebarCollapsed = uiStore((state) => state.sidebarCollapsed)
  const createNewSession = chatStore((state) => state.createNewSession)
  const navigate = useNavigate()

  const handleCreateNewChat = async () => {
    await createNewSession()
    navigate('/')
  }

  return (
    <header className={`${styles.header} ${sidebarCollapsed ? 'collapsed-mode' : ''}`}>
      {/* Mobile Toggle - Only visible on small screens */}
      <div className="header-left mobile-only">
        <button className="menu-toggle" onClick={toggleSidebar}>
          <MenuOutlined />
        </button>
      </div>

      {/* Collapsed Sidebar Controls - Visible when sidebar is collapsed on Desktop */}
      {sidebarCollapsed && (
        <div className="collapsed-controls">
           <div className="collapsed-actions-pill">
              <Button 
                type="text" 
                icon={<MenuUnfoldOutlined />} 
                className="collapsed-action-btn" 
                onClick={toggleSidebar}
              />
              <Button 
                type="text" 
                icon={<PlusOutlined />} 
                className="collapsed-action-btn"
                onClick={handleCreateNewChat}
              />
           </div>
        </div>
      )}
    </header>
  )
}
