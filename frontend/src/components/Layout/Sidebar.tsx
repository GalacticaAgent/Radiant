import { useEffect, useState } from 'react'
import {
  PlusOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  EllipsisOutlined,
  EditOutlined,
  PushpinOutlined,
  DeleteOutlined,
  ShareAltOutlined
} from '@ant-design/icons'
import { App, Button, Avatar, Dropdown, Modal, Input, MenuProps } from 'antd'
import { useNavigate } from 'react-router-dom'
import { uiStore, authStore, chatStore } from '../../store'
import styles from '../../styles/layout.module.css'
import './Sidebar.css'
import { Session } from '../../types/chat'

export default function Sidebar() {
  const { message, modal } = App.useApp()
  const navigate = useNavigate()
  const user = authStore((state) => state.user)
  const logout = authStore((state) => state.logout)
  const sidebarCollapsed = uiStore((state) => state.sidebarCollapsed)
  const toggleSidebar = uiStore((state) => state.toggleSidebar)
  
  const sessions = chatStore((state) => state.sessions)
  const fetchSessions = chatStore((state) => state.fetchSessions)
  const createNewSession = chatStore((state) => state.createNewSession)
  const renameSession = chatStore((state) => state.renameSession)
  const pinSession = chatStore((state) => state.pinSession)
  const deleteSession = chatStore((state) => state.deleteSession)
  const currentSessionId = chatStore((state) => state.currentSessionId)

  const [renameModalVisible, setRenameModalVisible] = useState(false)
  const [sessionToRename, setSessionToRename] = useState<Session | null>(null)
  const [newTitle, setNewTitle] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    fetchSessions(controller.signal)
    return () => controller.abort()
  }, [fetchSessions])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleCreateNewChat = async () => {
    await createNewSession()
    navigate('/')
    // Ensure active state is cleared if navigate('/') doesn't do it because id is undefined
    // Actually when we navigate to '/', routeSessionId is undefined.
    // currentSessionId will be the new ID.
    // The list items compare currentSessionId === item.id.
    // Since the new ID is not in the list yet (until we save it), no item will be active.
    // This is correct behavior for "New Chat" - no history item selected.
  }

  const handleRenameClick = (session: Session) => {
    setSessionToRename(session)
    setNewTitle(session.title)
    setRenameModalVisible(true)
  }

  const handleRenameSubmit = async () => {
    if (sessionToRename && newTitle.trim()) {
      await renameSession(sessionToRename.id, newTitle.trim())
      setRenameModalVisible(false)
      setSessionToRename(null)
      message.success('重命名成功')
    }
  }

  const handlePinClick = async (session: Session) => {
    await pinSession(session.id, !session.is_pinned)
  }
  
  const handleDeleteClick = (session: Session) => {
    modal.confirm({
      title: '确认删除',
      content: '确定要删除这个会话吗？删除后无法恢复。',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        await deleteSession(session.id)
        message.success('会话已删除')
        if (currentSessionId === session.id) {
            navigate('/')
        }
      }
    })
  }

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      label: '个人设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      label: '退出登录',
      danger: true,
      onClick: handleLogout,
    },
  ]

  // Grouping Logic
  const groupSessions = (sessions: Session[]) => {
    const groups: { title: string; items: Session[] }[] = []
    
    const pinned = sessions.filter((s) => s.is_pinned)
    const others = sessions.filter((s) => !s.is_pinned)
    
    if (pinned.length > 0) {
      groups.push({ title: '置顶', items: pinned })
    }
    
    const today = new Date()
    today.setHours(0,0,0,0)
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    const last7Days = new Date(today)
    last7Days.setDate(last7Days.getDate() - 7)
    const last30Days = new Date(today)
    last30Days.setDate(last30Days.getDate() - 30)
    
    const todayItems: Session[] = []
    const yesterdayItems: Session[] = []
    const last7DaysItems: Session[] = []
    const last30DaysItems: Session[] = []
    const olderItems: Session[] = []
    
    others.forEach(session => {
      const date = new Date(session.updated_at)
      date.setHours(0,0,0,0)
      
      if (date.getTime() === today.getTime()) {
        todayItems.push(session)
      } else if (date.getTime() === yesterday.getTime()) {
        yesterdayItems.push(session)
      } else if (date > last7Days) {
        last7DaysItems.push(session)
      } else if (date > last30Days) {
        last30DaysItems.push(session)
      } else {
        olderItems.push(session)
      }
    })
    
    if (todayItems.length > 0) groups.push({ title: '今天', items: todayItems })
    if (yesterdayItems.length > 0) groups.push({ title: '昨天', items: yesterdayItems })
    if (last7DaysItems.length > 0) groups.push({ title: '7天内', items: last7DaysItems })
    if (last30DaysItems.length > 0) groups.push({ title: '30天内', items: last30DaysItems })
    if (olderItems.length > 0) groups.push({ title: '更早', items: olderItems })
    
    return groups
  }

  const sessionGroups = groupSessions(sessions)
  const sidebarClass = `${styles.sidebar} ${sidebarCollapsed ? styles.collapsed : ''}`

  return (
    <aside className={sidebarClass}>
      <div className="sidebar-header">
        <div className="brand-container">
          {!sidebarCollapsed && (
            <div className="brand-logo">
              <span className="brand-text">Radiant</span>
            </div>
          )}
          <Button 
            type="text" 
            icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} 
            className="sidebar-menu-btn" 
            onClick={toggleSidebar}
          />
          {sidebarCollapsed && (
             <Button 
             type="text" 
             icon={<PlusOutlined />} 
             className="collapsed-new-chat-btn"
             onClick={handleCreateNewChat}
             title="开启新对话"
           />
          )}
        </div>
        
        {!sidebarCollapsed && (
          <Button 
            className="new-chat-btn" 
            icon={<PlusOutlined />}
            onClick={handleCreateNewChat}
          >
            开启新对话
          </Button>
        )}
      </div>

      {!sidebarCollapsed && (
        <div className="sidebar-content">
          {sessionGroups.map((section, idx) => (
            <div key={idx} className="history-section">
              <div className="section-title">{section.title}</div>
              <div className="section-list">
                {section.items.map(item => (
                  <div 
                    key={item.id} 
                    className={`history-item ${currentSessionId === item.id ? 'active' : ''}`}
                    onClick={() => {
                        // Optimistically set current session
                        navigate(`/chat/${item.id}`)
                    }}
                    // Note: onClick navigates, but we usually use Link or useNavigate
                    // I'll stick to onClick + navigate
                  >
                    {currentSessionId === item.id && <span className="active-dot"></span>}
                    <span 
                        className="item-title" 
                        onClick={(e) => {
                            e.stopPropagation()
                            navigate(item.id === currentSessionId ? '#' : `/chat/${item.id}`)
                            // Actually the parent div handles click, but we want title to be the main click target?
                            // No, whole row.
                            navigate(`/chat/${item.id}`)
                        }}
                    >
                        {item.title}
                    </span>
                    <div className="item-actions" onClick={(e) => e.stopPropagation()}>
                      <Dropdown 
                        menu={{ 
                            items: [
                                {
                                    key: 'rename',
                                    label: '重命名',
                                    icon: <EditOutlined />,
                                    onClick: () => handleRenameClick(item)
                                },
                                {
                                    key: 'pin',
                                    label: item.is_pinned ? '取消置顶' : '置顶',
                                    icon: <PushpinOutlined />,
                                    onClick: () => handlePinClick(item)
                                },
                                {
                                    key: 'share',
                                    label: '分享',
                                    icon: <ShareAltOutlined />,
                                    onClick: () => message.info('分享功能开发中')
                                },
                                {
                                    key: 'delete',
                                    label: '删除',
                                    icon: <DeleteOutlined />,
                                    danger: true,
                                    onClick: () => handleDeleteClick(item)
                                }
                            ]
                        }} 
                        trigger={['click']}
                        placement="bottomRight"
                      >
                        <EllipsisOutlined />
                      </Dropdown>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="sidebar-footer">
        <Dropdown menu={{ items: userMenuItems }} trigger={['click']}>
          <div className={`user-profile ${sidebarCollapsed ? 'collapsed' : ''}`}>
            <Avatar size="small" style={{ backgroundColor: '#4d6bfe' }}>
              {user?.username?.[0] || 'U'}
            </Avatar>
            {!sidebarCollapsed && (
              <>
                <span className="username">{user?.username || 'Guest'}</span>
                <Button type="text" icon={<EllipsisOutlined />} size="small" className="profile-menu-btn" />
              </>
            )}
          </div>
        </Dropdown>
      </div>

      <Modal
        title="重命名会话"
        open={renameModalVisible}
        onOk={handleRenameSubmit}
        onCancel={() => setRenameModalVisible(false)}
      >
        <Input 
            value={newTitle} 
            onChange={(e) => setNewTitle(e.target.value)} 
            placeholder="请输入新的会话标题"
            onPressEnter={handleRenameSubmit}
        />
      </Modal>
    </aside>
  )
}
