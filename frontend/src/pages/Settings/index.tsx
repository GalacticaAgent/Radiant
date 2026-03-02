import { useEffect, useState } from 'react'
import { AppLayout } from '../../components/Layout'
import { App, Button, Input, Spin } from 'antd'
import { userAPI, UserProfile } from '../../api/user'
import './Settings.css'

export default function Settings() {
  const { message } = App.useApp()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [apiKey, setApiKey] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const p = await userAPI.getProfile()
        setProfile(p)
        setApiKey(p.deepseek_api_key || '')
      } catch (e: any) {
        message.error(e?.response?.data?.detail || '加载用户资料失败')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const save = async () => {
    try {
      const updated = await userAPI.updateProfile({ deepseek_api_key: apiKey })
      setProfile(updated)
      message.success('已保存')
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '保存失败')
    }
  }

  return (
    <AppLayout>
      <div className="settings-container">
        <div className="settings-header">
          <h1>设置</h1>
          <p className="settings-subtitle">管理你的账户、隐私和订阅设置</p>
        </div>

        <section className="settings-section">
          <h2>账户概览</h2>
          {loading ? (
            <Spin />
          ) : profile ? (
            <>
              <p>用户名：{profile.username}</p>
              <p>邮箱：{profile.email}</p>
              <div style={{ maxWidth: 520 }}>
                <h3>DeepSeek API Key</h3>
                <Input.Password value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="输入 DeepSeek API Key" />
                <div style={{ marginTop: 12 }}>
                  <Button type="primary" onClick={save}>保存</Button>
                </div>
              </div>
            </>
          ) : (
            <p>未能加载用户资料</p>
          )}
        </section>

        <section className="settings-section">
          <h2>账户设置</h2>
          <p className="settings-description">管理你的个人账户信息和安全设置。</p>

          <h3>个人信息</h3>
          <p>更新你的姓名、邮箱和头像等个人信息。</p>
          <ul>
            <li>用户名</li>
            <li>邮箱地址</li>
            <li>头像设置</li>
          </ul>

          <h3>安全设置</h3>
          <p>管理密码和登录安全。</p>
          <ul>
            <li>修改密码</li>
            <li>两步验证</li>
            <li>登录历史</li>
            <li>活跃会话</li>
          </ul>
        </section>

        <section className="settings-section">
          <h2>隐私与通知</h2>
          <p className="settings-description">控制你的隐私设置和通知偏好。</p>

          <h3>隐私设置</h3>
          <p>设置谁可以看到你的研究和创意。</p>
          <ul>
            <li>研究公开度</li>
            <li>创意公开度</li>
            <li>论文公开度</li>
          </ul>

          <h3>通知偏好</h3>
          <p>选择接收通知的方式和时间。</p>
          <ul>
            <li>邮件通知</li>
            <li>网页通知</li>
            <li>通知频率</li>
          </ul>
        </section>

        <section className="settings-section">
          <h2>订阅与计费</h2>
          <p className="settings-description">管理你的订阅计划和支付信息。</p>

          <h3>当前订阅</h3>
          <p>查看和管理你的活跃订阅。</p>
          <ul>
            <li>订阅计划</li>
            <li>续费日期</li>
            <li>取消订阅</li>
          </ul>

          <h3>支付方式</h3>
          <p>添加和管理支付方式。</p>
          <ul>
            <li>信用卡</li>
            <li>PayPal</li>
            <li>发票历史</li>
          </ul>
        </section>

        <section className="settings-section">
          <h2>数据与隐私</h2>
          <p className="settings-description">管理你的数据和账户隐私。</p>

          <h3>数据导出</h3>
          <p>下载你的所有数据，包括研究、创意和论文。</p>

          <h3>账户删除</h3>
          <p>永久删除你的账户和所有相关数据。</p>
        </section>

        <section className="settings-section">
          <h2>应用设置</h2>
          <p className="settings-description">自定义应用的外观和行为。</p>

          <h3>外观主题</h3>
          <p>选择浅色或深色主题，或跟随系统设置。</p>
          <ul>
            <li>浅色模式</li>
            <li>深色模式</li>
            <li>自动（跟随系统）</li>
          </ul>

          <h3>语言和区域</h3>
          <p>设置应用的语言和时区。</p>
          <ul>
            <li>应用语言</li>
            <li>时区设置</li>
            <li>日期格式</li>
          </ul>
        </section>

        <section className="settings-section">
          <h2>帮助与支持</h2>
          <p className="settings-description">获取帮助和反馈。</p>

          <h3>常见问题</h3>
          <p>查看常见问题和答案。</p>

          <h3>联系支持</h3>
          <p>如有问题，请联系我们的支持团队。</p>

          <h3>版本信息</h3>
          <p>查看当前应用版本和更新日志。</p>
        </section>
      </div>
    </AppLayout>
  )
}
