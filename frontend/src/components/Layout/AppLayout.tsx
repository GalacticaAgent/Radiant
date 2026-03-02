import { ReactNode } from 'react'
import styles from '../../styles/layout.module.css'
import Header from './Header'
import Sidebar from './Sidebar'
import SideNavigation from './SideNavigation'
import { uiStore } from '../../store'
import './AppLayout.css'

interface AppLayoutProps {
  children: ReactNode
  showSideNavigation?: boolean
}

export default function AppLayout({ children, showSideNavigation = false }: AppLayoutProps) {
  const sidebarCollapsed = uiStore((state) => state.sidebarCollapsed)
  const layoutClass = `${styles.layout} ${sidebarCollapsed ? styles.collapsed : ''}`

  return (
    <div className={styles.container}>
      <div className={layoutClass}>
        <Header />
        <Sidebar />
        <main className={styles.main}>
          <div className={styles.content}>{children}</div>
        </main>
      </div>
      {showSideNavigation && <SideNavigation />}
    </div>
  )
}
