import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Card, App, Spin } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { authStore } from '../../store'
import { authAPI } from '../../api/auth'
import { RegisterRequest } from '../../types/auth'
import '../Login/Auth.css'

export default function Register() {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const { message } = App.useApp()
  const [loading, setLoading] = useState(false)
  const setUser = authStore((state) => state.setUser)
  const setToken = authStore((state) => state.setToken)
  const setRefreshToken = authStore((state) => state.setRefreshToken)

  const handleSubmit = async (values: RegisterRequest) => {
    setLoading(true)
    try {
      const response = await authAPI.register(values)
      setToken(response.access_token)
      setRefreshToken(response.refresh_token)
      setUser(response.user)
      message.success('Registration successful!')
      navigate('/')
    } catch (error: unknown) {
      const err = error as any
      const msg = err?.response?.data?.detail || err?.message || 'Registration failed. Please try again.'
      message.error(String(msg))
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
            <p>Create Your Account</p>
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
                prefix={<MailOutlined />}
                placeholder="your@email.com"
                size="large"
              />
            </Form.Item>

            <Form.Item
              name="username"
              label="Username"
              rules={[
                { required: true, message: 'Please enter a username' },
                { min: 3, message: 'Username must be at least 3 characters' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="username"
                size="large"
              />
            </Form.Item>

            <Form.Item
              name="password"
              label="Password"
              rules={[
                { required: true, message: 'Please enter a password' },
                { min: 8, message: 'Password must be at least 8 characters' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="••••••••"
                size="large"
              />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              label="Confirm Password"
              dependencies={['password']}
              rules={[
                { required: true, message: 'Please confirm your password' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve()
                    }
                    return Promise.reject(new Error('Passwords do not match'))
                  },
                }),
              ]}
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
                {loading ? <Spin size="small" /> : 'Create Account'}
              </Button>
            </Form.Item>
          </Form>

          <div className="auth-footer">
            <p>
              Already have an account?{' '}
              <Link to="/login" className="auth-link">
                Sign in
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}
