import { useEffect } from 'react'
import { BrowserRouter as Router } from 'react-router-dom'
import AppRouter from './router'
import { ConfigProvider, theme as antTheme, App as AntdApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { useTheme } from './hooks/useTheme'
import { authStore, uiStore } from './store'
import './styles/global.css'
import './styles/animations.css'
import './styles/components.css'

function AppContent() {
  const { theme } = useTheme()

  const antThemeConfig =
    theme === 'dark'
      ? {
          token: {
            colorPrimary: '#818cf8', // Indigo 400
            colorBgBase: '#0f172a', // Slate 900
            colorBgContainer: '#1e293b', // Slate 800
            colorBorder: '#334155',
            colorText: '#f8fafc',
            colorTextSecondary: '#cbd5e1',
            borderRadius: 12,
            fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            fontSize: 15,
          },
          components: {
            Card: {
              boxShadow: '0 10px 30px -10px rgba(0, 0, 0, 0.5)',
              colorBgContainer: 'rgba(30, 41, 59, 0.6)', // Semi-transparent for glass effect
              backdropFilter: 'blur(12px)',
            },
            Button: {
              borderRadius: 8,
              controlHeight: 40,
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
            },
            Input: {
              controlHeight: 42,
              borderRadius: 8,
              colorBgContainer: 'rgba(30, 41, 59, 0.4)',
              activeBorderColor: '#818cf8',
              hoverBorderColor: '#6366f1',
            },
            Layout: {
              bodyBg: '#020617',
              headerBg: 'rgba(15, 23, 42, 0.6)',
              siderBg: 'rgba(15, 23, 42, 0.6)',
            },
            Menu: {
              itemBg: 'transparent',
              itemColor: '#cbd5e1',
              itemSelectedColor: '#ffffff',
              itemSelectedBg: 'rgba(129, 140, 248, 0.15)',
              itemBorderRadius: 8,
              itemMarginInline: 8,
            },
          },
          algorithm: antTheme.darkAlgorithm,
        }
      : {
          token: {
            colorPrimary: '#4d6bfe', // DeepSeek Blue
            colorBgBase: '#ffffff',
            colorBgContainer: '#ffffff',
            colorBgLayout: '#ffffff',
            borderRadius: 12,
            fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            fontSize: 15,
          },
          components: {
            Card: {
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
              colorBgContainer: '#ffffff', 
              borderRadiusLG: 16,
            },
            Button: {
              borderRadius: 8,
              controlHeight: 40,
              boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
              primaryShadow: '0 4px 10px rgba(77, 107, 254, 0.2)',
            },
            Input: {
              controlHeight: 42,
              borderRadius: 8,
              colorBgContainer: '#ffffff',
              activeBorderColor: '#4d6bfe',
              hoverBorderColor: '#3b5bdb',
            },
            Layout: {
              bodyBg: '#ffffff',
              headerBg: '#ffffff',
              siderBg: '#f9fafb',
            },
            Menu: {
              itemBg: 'transparent',
              itemSelectedColor: '#4d6bfe',
              itemSelectedBg: '#eef2ff',
              itemBorderRadius: 8,
              itemMarginInline: 8,
            },
          },
          algorithm: antTheme.defaultAlgorithm,
        }

  return (
    <ConfigProvider locale={zhCN} theme={antThemeConfig}>
      <AntdApp>
        <Router>
          <AppRouter />
        </Router>
      </AntdApp>
    </ConfigProvider>
  )
}

function App() {
  useEffect(() => {
    // Hydrate auth and UI state from localStorage on app load
    authStore.getState().hydrate()
    uiStore.getState().hydrate()
  }, [])

  return <AppContent />
}

export default App
