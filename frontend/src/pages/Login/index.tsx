import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Card, App, Spin } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { authStore } from '../../store'
import { authAPI } from '../../api/auth'
import { LoginRequest } from '../../types/auth'
import './Auth.css'

export default function Login() {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const { message } = App.useApp()
  const [loading, setLoading] = useState(false)
  const setUser = authStore((state) => state.setUser)
  const setToken = authStore((state) => state.setToken)
  const setRefreshToken = authStore((state) => state.setRefreshToken)
  const logout = authStore((state) => state.logout)

  // Clear existing session when entering login page
  useEffect(() => {
    logout()
  }, [logout])

  const handleSubmit = async (values: LoginRequest) => {
    setLoading(true)
    try {
      const response = await authAPI.login(values)
      setToken(response.access_token)
      setRefreshToken(response.refresh_token)
      setUser(response.user)
      message.success('Login successful!')
      navigate('/')
    } catch (error: unknown) {
      const err = error as Record<string, unknown>
      const errorMessage = (err.message as string) || 'Login failed. Please try again.'
      message.error(errorMessage)
      
      // Only set password field error if it's likely an auth error
      if (errorMessage.toLowerCase().includes('password') || errorMessage.toLowerCase().includes('credential')) {
        form.setFields([
          {
            name: 'password',
            errors: ['Password is incorrect'],
          },
        ])
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <Card className="auth-card">
          <div className="auth-header">
            <h1>Radiant</h1>
            <p>Academic Research Assistant</p>
          </div>

          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            autoComplete="off"
          >
            <Form.Item
              name="email"
              label="Email"
              rules={[
                { required: true, message: 'Please enter your email' },
                { type: 'email', message: 'Please enter a valid email' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="your@email.com"
                size="large"
              />
            </Form.Item>

            <Form.Item
              name="password"
              label="Password"
              rules={[{ required: true, message: 'Please enter your password' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="••••••••"
                size="large"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                block
                size="large"
                loading={loading}
              >
                {loading ? <Spin size="small" /> : 'Login'}
              </Button>
            </Form.Item>
          </Form>

          <div className="auth-footer">
            <p>
              Don't have an account?{' '}
              <Link to="/register" className="auth-link">
                Sign up
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}
