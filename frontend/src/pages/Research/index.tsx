import { useEffect, useRef, useState } from 'react'
import { AppLayout } from '../../components/Layout'
import { App, Input, Card, Steps, Tabs, List, Tag, Typography, Empty, Spin, Progress } from 'antd'
import { RocketOutlined, FileTextOutlined, DeploymentUnitOutlined, UserOutlined } from '@ant-design/icons'
import { researchAPI, ResearchResult, TaskInfo } from '../../api/research'
import './Research.css'

const { Title, Paragraph } = Typography
const { Search } = Input

export default function Research() {
  const { message } = App.useApp()
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState(0)
  const [task, setTask] = useState<TaskInfo | null>(null)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [results, setResults] = useState<ResearchResult | null>(null)
  const pollRef = useRef<number | null>(null)

  const handleSearch = async (value: string) => {
    if (!value.trim()) return
    setLoading(true)
    setStep(0)
    setResults(null)
    setTask(null)
    setTaskId(null)

    try {
      const start = await researchAPI.start({ query: value.trim(), sources: ['knowledge_graph'], max_papers: 20 })
      setTaskId(start.task_id)
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '启动调研失败')
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!loading || !taskId) return

    const poll = async () => {
      try {
        const status = await researchAPI.status(taskId)
        setTask(status)

        if (status.progress >= 90) setStep(3)
        else if (status.progress >= 60) setStep(2)
        else if (status.progress >= 20) setStep(1)
        else setStep(0)

        if (status.status === 'completed') {
          const res = await researchAPI.result(taskId)
          setResults(res)
          setLoading(false)
          if (pollRef.current) window.clearInterval(pollRef.current)
          pollRef.current = null
        }

        if (status.status === 'failed') {
          message.error(status.error || '调研失败')
          setLoading(false)
          if (pollRef.current) window.clearInterval(pollRef.current)
          pollRef.current = null
        }
      } catch (e: any) {
        message.error(e?.response?.data?.detail || '查询调研状态失败')
        setLoading(false)
        if (pollRef.current) window.clearInterval(pollRef.current)
        pollRef.current = null
      }
    }

    poll()
    pollRef.current = window.setInterval(poll, 1500)
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [loading, taskId])

  return (
    <AppLayout>
      <div className="research-page">
        <div className={`search-section ${results ? 'compact' : ''}`}>
          <div className="search-header">
            <Title level={2} style={{ marginBottom: 0 }}>Research Discovery</Title>
            {!results && <Paragraph type="secondary">Explore academic frontiers with AI-powered insights</Paragraph>}
          </div>
          
          <Search
            placeholder="Enter a research topic (e.g., 'Large Language Models for Coding')"
            allowClear
            enterButton="Start Research"
            size="large"
            onSearch={handleSearch}
            loading={loading}
            className="research-search-input"
          />
        </div>

        {loading && (
          <div className="progress-section">
            <Card>
              <Steps
                current={step}
                items={[
                  { title: 'Initializing', icon: <RocketOutlined /> },
                  { title: 'Crawling Sources', description: 'ArXiv, Google Scholar' },
                  { title: 'Analyzing Data', description: 'Extracting entities & relations' },
                  { title: 'Generating Report', description: 'Synthesizing insights' },
                ]}
              />
              <div style={{ marginTop: 24, textAlign: 'center' }}>
                <Spin tip={task?.message || 'AI agents are working hard...'} size="large" />
                {typeof task?.progress === 'number' && (
                  <div style={{ maxWidth: 520, margin: '16px auto 0' }}>
                    <Progress percent={task.progress} />
                  </div>
                )}
              </div>
            </Card>
          </div>
        )}

        {results && !loading && (
          <div className="results-section fade-in">
            <div className="summary-card">
              <Card title={<><RocketOutlined /> AI Executive Summary</>} variant="borderless" className="highlight-card">
                <Paragraph>{results.summary}</Paragraph>
                <div className="keywords">
                  {results.key_trends.slice(0, 8).map((k: string) => <Tag color="blue" key={k}>{k}</Tag>)}
                </div>
              </Card>
            </div>

            <Tabs
              defaultActiveKey="papers"
              items={[
                {
                  key: 'papers',
                  label: <span><FileTextOutlined /> Related Papers ({results.papers.length})</span>,
                  children: (
                    <List
                      grid={{ gutter: 16, column: 1 }}
                      dataSource={results.papers}
                      renderItem={(item: any) => (
                        <List.Item>
                          <Card hoverable className="paper-card">
                            <div className="paper-header">
                              <Title level={5}>
                                {item.url ? (
                                  <a href={item.url} target="_blank" rel="noreferrer">{item.title}</a>
                                ) : (
                                  item.title
                                )}
                              </Title>
                              {item.published_year && <Tag color={item.published_year > 2023 ? 'green' : 'default'}>{item.published_year}</Tag>}
                            </div>
                            <Paragraph ellipsis={{ rows: 2 }} type="secondary">{item.summary}</Paragraph>
                            <div className="paper-footer">
                              <div className="authors">
                                <UserOutlined /> {item.authors?.join(', ') || 'Unknown'}
                              </div>
                              <div className="venue">{item.venue || ''}</div>
                            </div>
                          </Card>
                        </List.Item>
                      )}
                    />
                  ),
                },
                {
                  key: 'graph',
                  label: <span><DeploymentUnitOutlined /> Knowledge Graph</span>,
                  children: (
                    <div className="graph-placeholder">
                      <Empty description="Knowledge Graph Visualization will be rendered here" />
                    </div>
                  ),
                },
              ]}
            />
          </div>
        )}
      </div>
    </AppLayout>
  )
}
