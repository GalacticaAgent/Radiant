import { useState } from 'react'
import { AppLayout } from '../../components/Layout'
import { App, Input, Button, Card, Row, Col, Statistic, Progress, Typography, List, Tag } from 'antd'
import { BulbOutlined, CheckCircleOutlined, CloseCircleOutlined, ArrowRightOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { ideaAPI, IdeaValidationResult } from '../../api/idea'
import './IdeaValidation.css'

const { Title, Paragraph, Text } = Typography
const { TextArea } = Input

export default function IdeaValidation() {
  const { message } = App.useApp()
  const [idea, setIdea] = useState('')
  const [validating, setValidating] = useState(false)
  const [result, setResult] = useState<IdeaValidationResult | null>(null)

  const handleValidate = async () => {
    if (!idea.trim()) return
    setValidating(true)

    try {
      const res = await ideaAPI.validate(idea.trim())
      setResult(res)
    } catch (e: any) {
      message.error(e?.response?.data?.detail || 'Idea 校验失败')
    } finally {
      setValidating(false)
    }
  }

  return (
    <AppLayout>
      <div className="idea-page">
        {!result ? (
          <div className="idea-input-section fade-in">
            <div className="idea-header">
              <div className="icon-wrapper">
                <BulbOutlined />
              </div>
              <Title level={2}>Validate Your Research Idea</Title>
              <Paragraph type="secondary" style={{ fontSize: '1.1rem' }}>
                Get instant feedback on novelty, feasibility, and potential impact.
              </Paragraph>
            </div>

            <Card className="input-card" variant="borderless">
              <TextArea
                value={idea}
                onChange={(e) => setIdea(e.target.value)}
                placeholder="Describe your research idea in detail... (e.g., 'I want to use Graph Neural Networks to optimize compiler instruction scheduling by representing the control flow graph as input...')"
                autoSize={{ minRows: 6, maxRows: 12 }}
                className="idea-textarea"
                disabled={validating}
              />
              <div className="input-footer">
                <Button 
                  type="primary" 
                  size="large" 
                  onClick={handleValidate} 
                  loading={validating}
                  icon={!validating && <ArrowRightOutlined />}
                  className="validate-button"
                  disabled={!idea.trim()}
                >
                  {validating ? 'Analyzing Feasibility...' : 'Validate Idea'}
                </Button>
              </div>
            </Card>
          </div>
        ) : (
          <div className="report-section fade-in">
             <div className="report-header">
                <Button onClick={() => setResult(null)} type="text">← Validate another idea</Button>
                <Title level={3} style={{ margin: '16px 0' }}>Feasibility Report</Title>
             </div>

             <Row gutter={[24, 24]}>
               <Col xs={24} md={8}>
                 <Card className="score-card">
                   <Statistic
                     title="Feasibility Score"
                     value={Math.round(result.feasibility_score * 10)}
                     suffix="/ 100"
                     valueStyle={{ color: '#52c41a', fontSize: '3rem' }}
                     prefix={<SafetyCertificateOutlined />}
                   />
                   <Progress percent={Math.round(result.feasibility_score * 10)} showInfo={false} strokeColor="#52c41a" />
                   <Paragraph type="secondary" style={{ marginTop: 16 }}>
                     {result.feasibility_score >= 7 ? '可行性较高，建议继续推进。' : '可行性一般，建议先缩小问题或补充证据。'}
                   </Paragraph>
                 </Card>
               </Col>

               <Col xs={24} md={16}>
                 <Card title="Novelty Assessment" className="novelty-card">
                   <Paragraph>{result.detailed_analysis}</Paragraph>
                   <div className="tags-container">
                     {result.research_directions.map((t: string) => <Tag key={t}>{t}</Tag>)}
                   </div>
                 </Card>
               </Col>

               <Col xs={24} md={12}>
                 <Card title={<span style={{ color: '#52c41a' }}><CheckCircleOutlined /> Supporting Evidence</span>}>
                   <List
                     dataSource={result.strengths}
                     renderItem={(item: any) => (
                       <List.Item>
                         <Text><CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} /> {item}</Text>
                       </List.Item>
                     )}
                   />
                 </Card>
               </Col>

               <Col xs={24} md={12}>
                 <Card title={<span style={{ color: '#ff4d4f' }}><CloseCircleOutlined /> Potential Challenges</span>}>
                   <List
                     dataSource={result.challenges}
                     renderItem={(item: any) => (
                       <List.Item>
                         <Text><CloseCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} /> {item}</Text>
                       </List.Item>
                     )}
                   />
                 </Card>
               </Col>

               <Col xs={24}>
                 <Card title="Suggestions for Improvement" className="suggestions-card">
                   <List
                     dataSource={result.recommendations}
                     renderItem={(item: any, index: number) => (
                       <List.Item>
                         <Text strong style={{ marginRight: 8 }}>{index + 1}.</Text> {item}
                       </List.Item>
                     )}
                   />
                 </Card>
               </Col>
             </Row>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
