import { Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { authStore } from './store'
import { Spin } from 'antd'
import Login from './pages/Login'
import Register from './pages/Register'

// Lazy load pages
const Home = lazy(() => import('./pages/Home'))
const Research = lazy(() => import('./pages/Research'))
const IdeaValidation = lazy(() => import('./pages/IdeaValidation'))
const PaperPolish = lazy(() => import('./pages/PaperPolish'))
const KnowledgeGraph = lazy(() => import('./pages/KnowledgeGraph'))
const Settings = lazy(() => import('./pages/Settings'))
const FormatReviewBoard = lazy(() => import('./pages/FormatReviewBoard'))

// Protected Route Component
interface ProtectedRouteProps {
  element: React.ReactElement
}

function ProtectedRoute({ element }: ProtectedRouteProps) {
  const isAuthenticated = authStore((state) => state.isAuthenticated)

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <Suspense
      fallback={
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
          <Spin size="large" />
        </div>
      }
    >
      {element}
    </Suspense>
  )
}

// Public Route Component with redirect if already authenticated
interface PublicRouteProps {
  element: React.ReactElement
}

function PublicRoute({ element }: PublicRouteProps) {
  return element
}

const AppRouter = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<PublicRoute element={<Login />} />} />
      <Route path="/register" element={<PublicRoute element={<Register />} />} />

      {/* Protected routes */}
      <Route path="/" element={<ProtectedRoute element={<Home />} />} />
      <Route path="/chat/:id" element={<ProtectedRoute element={<Home />} />} />
      <Route path="/format-review/:sessionId" element={<ProtectedRoute element={<FormatReviewBoard />} />} />
      <Route path="/research" element={<ProtectedRoute element={<Research />} />} />
      <Route path="/idea-validation" element={<ProtectedRoute element={<IdeaValidation />} />} />
      <Route path="/paper-polish" element={<ProtectedRoute element={<PaperPolish />} />} />
      <Route path="/knowledge-graph" element={<ProtectedRoute element={<KnowledgeGraph />} />} />
      <Route path="/settings" element={<ProtectedRoute element={<Settings />} />} />

      {/* Catch all - redirect to home or login */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default AppRouter
