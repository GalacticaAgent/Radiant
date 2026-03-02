import { useEffect, useMemo, useState } from 'react'
import { Alert, App, Button, Card, Col, Empty, Input, Modal, Progress, Row, Select, Space, Spin, Table, Tabs, Tag, Typography, Upload } from 'antd'
import type { UploadFile } from 'antd'
import { 
  CloudUploadOutlined, 
  FileTextOutlined, 
  HistoryOutlined, 
  InboxOutlined, 
  SettingOutlined,
  RocketOutlined,
  CopyOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EditOutlined,
  BranchesOutlined,
  PushpinOutlined,
  PushpinFilled
} from '@ant-design/icons'
import { formatReviewAPI, FormatReviewHistoryItem } from '../../api/formatReview'
import { ruleAPI, RuleDetail, RuleItem, RuleVersionItem } from '../../api/rule'
import { systemAPI } from '../../api/system'
import '../../pages/FormatReviewBoard/index.css'

const { Text } = Typography

type Props = {
  sessionId: string
  incoming?: {
    paperId?: string | null
    paperFilename?: string | null
    file?: File | null
    text?: string | null
  }
  initialActive?: 'review' | 'history' | 'rules' | null
  onAppendToChat?: (content: string) => void
}

type PersistedDraft = {
  paperId: string | null
  paperFilename: string | null
  text: string | null
}

const draftKey = (sid: string) => `formatReviewBoard:draft:${sid}`
const activeKey = (sid: string) => `formatReviewBoard:active:${sid}`

export default function FormatReviewBoardCore({ sessionId, incoming, initialActive, onAppendToChat }: Props) {
  const { message, modal } = App.useApp()
  const sid = sessionId

  const toErrorMessage = (e: any, fallback: string) => {
    const detail = e?.response?.data?.detail ?? e?.response?.data?.message ?? e?.message
    if (typeof detail === 'string' && detail.trim()) return detail
    if (Array.isArray(detail)) {
      const parts = detail
        .map((x) => (typeof x === 'string' ? x : x?.msg || x?.message || JSON.stringify(x)))
        .map((x) => String(x || '').trim())
        .filter(Boolean)
      if (parts.length) return parts.join('；')
    }
    if (detail && typeof detail === 'object') {
      const msg = (detail as any).msg || (detail as any).message
      if (typeof msg === 'string' && msg.trim()) return msg
      try {
        return JSON.stringify(detail)
      } catch {}
    }
    return fallback
  }

  const loading = false
  const error: string | null = null
  const [active, setActive] = useState<'review' | 'history' | 'rules'>(() => {
    if (initialActive === 'history' || initialActive === 'rules' || initialActive === 'review') return initialActive
    try {
      const raw = sessionStorage.getItem(activeKey(sid))
      if (raw === 'history' || raw === 'rules' || raw === 'review') return raw
    } catch {}
    return 'review'
  })

  const [paperFilename, setPaperFilename] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [uploadId, setUploadId] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadPercent, setUploadPercent] = useState(0)
  const [uploadState, setUploadState] = useState<string | null>(null)
  const [reviewTaskId, setReviewTaskId] = useState<string | null>(null)
  const [reviewStatus, setReviewStatus] = useState<string | null>(null)
  const [reviewProgress, setReviewProgress] = useState<number>(0)
  const [historyItems, setHistoryItems] = useState<FormatReviewHistoryItem[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [rules, setRules] = useState<RuleItem[]>([])
  const [rulesLoading, setRulesLoading] = useState(false)
  const [selectedRule, setSelectedRule] = useState<string | null>(null)
  const [manageRuleId, setManageRuleId] = useState<string | null>(null)
  const [manageRuleDetail, setManageRuleDetail] = useState<RuleDetail | null>(null)
  const [manageRuleVersions, setManageRuleVersions] = useState<RuleVersionItem[]>([])
  const [manageVersionOpen, setManageVersionOpen] = useState(false)
  const [manageVersionContent, setManageVersionContent] = useState<any | null>(null)
  const [renameOpen, setRenameOpen] = useState(false)
  const [renameValue, setRenameValue] = useState('')
  const [skillRenameOpen, setSkillRenameOpen] = useState(false)
  const [skillRenameValue, setSkillRenameValue] = useState('')
  const [rulePreviewMode, setRulePreviewMode] = useState<'skill' | 'json'>('skill')
  const [ruleFile, setRuleFile] = useState<File | null>(null)
  const [ruleFileId, setRuleFileId] = useState<string | null>(null)
  const [ruleGenTaskId, setRuleGenTaskId] = useState<string | null>(null)
  const [ruleGenStatus, setRuleGenStatus] = useState<string | null>(null)

  const rulesCacheKey = `formatReviewBoard:rules:v1`
  const rulesCacheTtlMs = 5 * 60 * 1000

  useEffect(() => {
    try {
      sessionStorage.setItem(activeKey(sid), active)
    } catch {}
  }, [active, sid])

  useEffect(() => {
    const incomingDraft: PersistedDraft = {
      paperId: incoming?.paperId ?? null,
      paperFilename: incoming?.paperFilename ?? null,
      text: incoming?.text ?? null,
    }
    if (incomingDraft.paperId || incomingDraft.text) {
      setPaperFilename(incomingDraft.paperFilename)
      try {
        sessionStorage.setItem(draftKey(sid), JSON.stringify(incomingDraft))
      } catch {}
    } else {
      try {
        const raw = sessionStorage.getItem(draftKey(sid))
        if (raw) {
          const parsed = JSON.parse(raw) as PersistedDraft
          setPaperFilename(parsed.paperFilename ?? null)
        }
      } catch {}
    }
    setFile(incoming?.file ?? null)
  }, [sid, incoming?.paperId, incoming?.paperFilename, incoming?.text, incoming?.file])

  const uploadFileList: UploadFile[] = useMemo(() => {
    if (!file) return []
    const st =
      uploadState === 'failed'
        ? 'error'
        : uploadState === 'ready'
          ? 'done'
          : uploading || uploadState === 'uploading' || uploadState === 'verifying'
            ? 'uploading'
            : 'done'
    return [{ uid: '1', name: file.name, status: st as any, size: file.size }]
  }, [file, uploadState, uploading])

  const runUpload = async (): Promise<string> => {
    if (!file) throw new Error('未选择文件')
    setUploading(true)
    setUploadPercent(0)
    setUploadState('init')
    try {
      const init = await formatReviewAPI.initUpload({ session_id: sid, filename: file.name, size: file.size, mime_type: file.type || null })
      const nextUploadId = init.upload_id
      setUploadId(nextUploadId)
      setUploadState('uploading')
      const chunkSize = init.chunk_size
      const totalParts = init.expected_parts || Math.ceil(file.size / chunkSize)
      for (let i = 0; i < totalParts; i++) {
        const start = i * chunkSize
        const end = Math.min(file.size, start + chunkSize)
        const chunk = await file.slice(start, end).arrayBuffer()
        let ok = false
        for (let attempt = 1; attempt <= 3; attempt++) {
          try {
            await formatReviewAPI.uploadPart(nextUploadId, i + 1, chunk)
            ok = true
            break
          } catch {
            await new Promise((r) => window.setTimeout(r, 400 * attempt))
          }
        }
        if (!ok) throw new Error(`上传分片失败：part=${i + 1}`)
        setUploadPercent(Math.floor(((i + 1) / totalParts) * 90))
      }
      setUploadState('verifying')
      try {
        await formatReviewAPI.completeUpload(nextUploadId)
      } catch (e: any) {
        const detail = e?.response?.data?.detail || ''
        if (String(detail).toLowerCase().includes('missing parts')) {
          return await resumeUpload(nextUploadId)
        }
        throw e
      }
      const st = await formatReviewAPI.uploadStatus(nextUploadId)
      if (st.status !== 'ready') {
        return await resumeUpload(nextUploadId)
      }
      setUploadState('ready')
      setUploadPercent(100)
      return nextUploadId
    } catch (e: any) {
      setUploadState('failed')
      setUploadPercent(0)
      throw new Error(e?.response?.data?.detail || e?.message || '上传失败')
    } finally {
      setUploading(false)
    }
  }

  const resumeUpload = async (existingUploadId: string): Promise<string> => {
    if (!file) throw new Error('未选择文件')
    setUploading(true)
    setUploadPercent(0)
    setUploadState('uploading')
    try {
      let lastMissing: number[] | null = null
      let lastExpected: number | null = null
      let lastReceived: number | null = null
      for (let round = 0; round < 6; round++) {
        const st = await formatReviewAPI.uploadStatus(existingUploadId)
        if (st.status === 'ready') {
          setUploadState('ready')
          setUploadPercent(100)
          return existingUploadId
        }
        if (st.status !== 'uploading' && st.status !== 'uploaded') {
          return await runUpload()
        }
        if (typeof st.size === 'number' && st.size > 0 && st.size !== file.size) {
          return await runUpload()
        }
        const chunkSize = st.chunk_size
        const totalParts = st.expected_parts || Math.ceil(file.size / chunkSize)
        const uploaded = new Set((st.uploaded_parts || []).map((x) => Number(x)).filter((x) => Number.isFinite(x) && x >= 1))
        const missingList = Array.isArray(st.missing_parts) && st.missing_parts.length ? st.missing_parts : null
        const toUpload = missingList ? missingList : Array.from({ length: totalParts }, (_, i) => i + 1).filter((p) => !uploaded.has(p))
        lastMissing = missingList
        lastExpected = totalParts
        lastReceived = uploaded.size
        for (const part of toUpload) {
          const start = (part - 1) * chunkSize
          const end = Math.min(file.size, start + chunkSize)
          const chunk = await file.slice(start, end).arrayBuffer()
          let ok = false
          for (let attempt = 1; attempt <= 3; attempt++) {
            try {
              await formatReviewAPI.uploadPart(existingUploadId, part, chunk)
              ok = true
              break
            } catch {
              await new Promise((r) => window.setTimeout(r, 400 * attempt))
            }
          }
          if (!ok) throw new Error(`上传分片失败：part=${part}`)
          uploaded.add(part)
          setUploadPercent(Math.floor((uploaded.size / totalParts) * 90))
        }
        setUploadState('verifying')
        try {
          await formatReviewAPI.completeUpload(existingUploadId)
          setUploadState('ready')
          setUploadPercent(100)
          return existingUploadId
        } catch (e: any) {
          const detail = e?.response?.data?.detail || ''
          if (String(detail).toLowerCase().includes('missing parts')) {
            await new Promise((r) => window.setTimeout(r, 600 + round * 500))
            setUploadState('uploading')
            continue
          }
          throw e
        }
      }
      const missingHint = lastMissing?.length ? `，缺失分片：${lastMissing.slice(0, 20).join(', ')}${lastMissing.length > 20 ? '…' : ''}` : ''
      const progressHint = lastExpected && lastReceived !== null ? `（${lastReceived}/${lastExpected}）` : ''
      throw new Error(`上传未完成：缺少分片${progressHint}${missingHint}`)
    } catch (e: any) {
      setUploadState('failed')
      setUploadPercent(0)
      throw new Error(e?.response?.data?.detail || e?.message || '上传失败')
    } finally {
      setUploading(false)
    }
  }

  const startReview = async () => {
    if (!selectedRule) return
    if (uploading) {
      message.info('文件上传中，请稍候…')
      return
    }
    if (!uploadId && !file) {
      message.info('请先选择 PDF/DOCX/DOC 文件')
      return
    }
    try {
      let ensuredUploadId: string
      if (uploadId) {
        try {
          const st = await formatReviewAPI.uploadStatus(uploadId)
          if (st.status === 'ready') {
            setUploadState('ready')
            setUploadPercent(100)
            ensuredUploadId = uploadId
          } else {
            setUploadState(st.status as any)
            ensuredUploadId = await resumeUpload(uploadId)
          }
        } catch {
          ensuredUploadId = await resumeUpload(uploadId)
        }
      } else {
        ensuredUploadId = await runUpload()
      }
      const res = await formatReviewAPI.start({
        session_id: sid,
        upload_id: ensuredUploadId,
        rule_id: selectedRule === '__default__' ? null : selectedRule,
        paper_title: paperFilename || file?.name || null,
        filename: file?.name || paperFilename || null,
      })
      setReviewTaskId(res.task_id)
      setReviewStatus('queued')
      setReviewProgress(0)
      message.success('已开始审查，正在生成报告…')
    } catch (e: any) {
      const detail = e?.response?.data?.detail || ''
      if (String(detail).startsWith('upload not ready:') && uploadId) {
        try {
          await resumeUpload(uploadId)
          const res2 = await formatReviewAPI.start({
            session_id: sid,
            upload_id: uploadId,
            rule_id: selectedRule === '__default__' ? null : selectedRule,
            paper_title: paperFilename || file?.name || null,
            filename: file?.name || paperFilename || null,
          })
          setReviewTaskId(res2.task_id)
          setReviewStatus('queued')
          setReviewProgress(0)
          message.success('已开始审查，正在生成报告…')
          return
        } catch {
        }
      }
      message.error(toErrorMessage(e, '开始审查失败'))
    }
  }

  const loadRules = async (force: boolean = false) => {
    setRulesLoading(true)
    try {
      if (!force) {
        try {
          const cached = localStorage.getItem(rulesCacheKey)
          if (cached) {
            const parsed = JSON.parse(cached) as { ts: number; items: RuleItem[] }
            if (parsed?.ts && Date.now() - parsed.ts < rulesCacheTtlMs && Array.isArray(parsed.items)) {
              setRules(parsed.items)
              if (!selectedRule) {
                setSelectedRule('__default__')
              }
              setRulesLoading(false)
              return
            }
          }
        } catch {}
      }
      const res = await ruleAPI.my()
      const items = res.items || []
      setRules(items)
      if (!selectedRule) {
        setSelectedRule('__default__')
      }
      try {
        localStorage.setItem(rulesCacheKey, JSON.stringify({ ts: Date.now(), items }))
      } catch {}
    } catch (e: any) {
      message.error(toErrorMessage(e, '加载规则失败'))
    } finally {
      setRulesLoading(false)
    }
  }

  const loadRuleDetail = async (ruleId: string) => {
    try {
      const d = await ruleAPI.detail(ruleId)
      setManageRuleDetail(d)
      setManageRuleId(ruleId)
      const hasSkill = !!(d as any)?.content?.skill?.markdown
      setRulePreviewMode(hasSkill ? 'skill' : 'json')
    } catch (e: any) {
      message.error(toErrorMessage(e, '加载规则详情失败'))
    }
  }

  useEffect(() => {
    if (active === 'review' || active === 'rules') loadRules(active === 'rules')
  }, [active])

  useEffect(() => {
    if (active !== 'rules') return
    if (!manageRuleId && rules.length) {
      setManageRuleId(rules[0].rule_id)
      loadRuleDetail(rules[0].rule_id)
    }
  }, [active, rules])

  useEffect(() => {
    if (!reviewTaskId) return
    let stopped = false
    const tick = async () => {
      try {
        const t = await formatReviewAPI.getTask(reviewTaskId)
        if (stopped) return
        setReviewStatus(t.status)
        setReviewProgress(t.progress)
        if (t.status === 'done') {
          const rawMd = String((t as any)?.result?.markdown || '').trim()
          if (rawMd && typeof onAppendToChat === 'function') {
            const lines = rawMd.split(/\r?\n/)
            const start = lines.findIndex((x) => /^###\s*1\./.test(x))
            const idx8 = lines.findIndex((x) => /^###\s*8\./.test(x))
            let sliced = rawMd
            if (start >= 0) {
              if (idx8 >= 0) {
                let end = lines.length
                for (let i = idx8 + 1; i < lines.length; i++) {
                  if (/^###\s*\d+\./.test(lines[i])) {
                    end = i
                    break
                  }
                }
                sliced = lines.slice(start, end).join('\n').trim()
              } else {
                sliced = lines.slice(start).join('\n').trim()
              }
            }
            if (sliced) onAppendToChat(sliced)
          }
          const saved = await formatReviewAPI.saveHistory(reviewTaskId)
          message.success(`审查完成，已写入历史（${saved.history_id}）`)
          setActive('history')
          setReviewTaskId(null)
          return
        }
        if (t.status === 'failed') {
          message.error(t.error || '审查失败')
          setReviewTaskId(null)
          return
        }
      } catch {}
      window.setTimeout(tick, 1500)
    }
    window.setTimeout(tick, 800)
    return () => {
      stopped = true
    }
  }, [reviewTaskId])

  const loadHistory = async () => {
    setHistoryLoading(true)
    try {
      const res = await formatReviewAPI.listHistory(sid, 1, 10)
      setHistoryItems(res.items || [])
    } catch (e: any) {
      message.error(toErrorMessage(e, '加载历史失败'))
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    if (active === 'history') loadHistory()
  }, [active, sid])

  useEffect(() => {
    if (!ruleGenTaskId) return
    let stopped = false
    let inFlight: AbortController | null = null
    const startedAt = Date.now()
    let delay = 800
    let warned = false
    const tick = async () => {
      if (stopped) return
      if (Date.now() - startedAt > 45000) {
        if (!warned) {
          warned = true
          try {
            const hc = await systemAPI.health()
            if (hc.celery_run_inline === false && (!hc.worker_ok || !hc.broker_ok)) {
              message.warning('后台任务队列未就绪：规则生成可能长时间排队')
            } else {
              message.warning('规则生成通常需要 30-90 秒，请耐心等待或稍后在“规则管理”中查看')
            }
          } catch {
            message.warning('规则生成通常需要 30-90 秒，请耐心等待')
          }
        }
      }
      try {
        inFlight?.abort()
        inFlight = new AbortController()
        const st = await ruleAPI.task(ruleGenTaskId, { signal: inFlight.signal })
        if (stopped) return
        setRuleGenStatus(st.status)
        if (st.status === 'done' && st.rule_id) {
          setRuleGenTaskId(null)
          setRuleGenStatus(null)
          setRuleFile(null)
          setRuleFileId(null)
          try {
            localStorage.removeItem(rulesCacheKey)
          } catch {}
          await loadRules(true)
          await loadRuleDetail(st.rule_id)
          message.success('规则生成完成')
          return
        }
        if (st.status === 'failed') {
          setRuleGenTaskId(null)
          message.error(st.error || '规则生成失败')
          return
        }
      } catch {}
      delay = Math.min(8000, Math.round(delay * 1.25))
      window.setTimeout(tick, delay)
    }
    window.setTimeout(tick, 800)
    return () => {
      stopped = true
      inFlight?.abort()
    }
  }, [ruleGenTaskId])

  const reviewPane = (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <Row gutter={[24, 24]}>
        <Col xs={24} md={12}>
          <Card 
            className="frb-card" 
            title={<Space><CloudUploadOutlined /><span>上传论文</span></Space>}
          >
            <Upload.Dragger
              className="frb-upload-dragger"
              multiple={false}
              fileList={uploadFileList}
              beforeUpload={(f) => {
                const ext = (f.name || '').toLowerCase()
                const ok = ext.endsWith('.pdf') || ext.endsWith('.docx') || ext.endsWith('.doc')
                if (!ok) {
                  message.error('仅支持 .pdf / .docx / .doc')
                  return Upload.LIST_IGNORE
                }
                if ((f as any).size && (f as any).size > 50 * 1024 * 1024) {
                  message.error('单文件大小不能超过 50MB')
                  return Upload.LIST_IGNORE
                }
                setFile(f as unknown as File)
                setUploadId(null)
                setUploadState(null)
                setUploadPercent(0)
                return false
              }}
              onRemove={() => {
                setFile(null)
                setUploadId(null)
                setUploadState(null)
                setUploadPercent(0)
                return true
              }}
            >
              <p className="frb-upload-icon"><InboxOutlined /></p>
              <p className="frb-upload-text">拖拽文件到此处，或点击选择文件</p>
              <p className="frb-upload-hint">支持 .pdf / .docx / .doc，单文件 ≤50MB</p>
            </Upload.Dragger>
            {uploadState && (
              <div className="frb-mt-sm">
                <Text type="secondary">状态：{uploadState}</Text>
              </div>
            )}
            {import.meta.env.DEV && (
              <div className="frb-mt-sm">
                <Text type="secondary">API：{import.meta.env.VITE_API_BASE_URL || '/api/v1'}</Text>
              </div>
            )}
            {(uploading || uploadPercent > 0) && (
              <Progress percent={uploadPercent} size="small" status={uploadState === 'failed' ? 'exception' : 'active'} className="frb-mt-sm" />
            )}
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card 
            className="frb-card" 
            title={<Space><FileTextOutlined /><span>选择审查规则</span></Space>}
          >
            <Select
              className="frb-rule-select"
              placeholder="请选择审查规则"
              loading={rulesLoading}
              value={selectedRule ?? undefined}
              onChange={(v) => setSelectedRule(v)}
              options={[
                { value: '__default__', label: '默认学术论文规则（系统内置）' },
                ...rules
                  .slice()
                  .sort((a, b) => Number(b.pinned) - Number(a.pinned))
                  .map((r) => ({ 
                    value: r.rule_id, 
                    label: (
                      <Space>
                        {r.pinned && <PushpinFilled style={{ color: '#1677ff' }} />}
                        <span>{r.name}</span>
                        <Tag bordered={false}>v{r.version}</Tag>
                      </Space>
                    )
                  })),
              ]}
            />
            {!rules.length && (
              <Alert 
                type="warning" 
                showIcon 
                message="未检测到自定义规则" 
                description="已为您加载系统内置的默认学术论文审查规则。" 
                className="frb-mt-md" 
              />
            )}
            <div className="frb-mt-md">
              <Text type="secondary" style={{ fontSize: 13 }}>
                * 规则决定了审查的侧重点，您可以随时在"自定义规则"页签中创建专属规则。
              </Text>
            </div>
          </Card>
        </Col>
        
        <Col span={24}>
          <div className="frb-action-area">
            {reviewTaskId ? (
              <div className="frb-progress-area">
                <div className="frb-progress-text">
                  <Spin size="small" style={{ marginRight: 8 }} />
                  正在生成审查报告 (taskId: {reviewTaskId})
                </div>
                <Progress percent={reviewProgress} status="active" strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }} />
                <div className="frb-mt-sm">
                  <Tag color="processing">{reviewStatus || 'PROCESSING'}</Tag>
                </div>
              </div>
            ) : (
              <Button 
                type="primary" 
                className="frb-start-btn"
                icon={<RocketOutlined />}
                size="large"
                disabled={!selectedRule || (!file && !uploadId) || uploading} 
                onClick={startReview}
              >
                开始审查
              </Button>
            )}
          </div>
        </Col>
      </Row>
    </div>
  )

  const historyPane = (
    <Card className="frb-card" title={<Space><HistoryOutlined /><span>本会话审查历史</span></Space>}>
      <Table
        rowKey="history_id"
        loading={historyLoading}
        dataSource={historyItems}
        pagination={false}
        columns={[
          { 
            title: '论文标题', 
            dataIndex: 'paper_title', 
            key: 'paper_title', 
            render: (v) => <Text strong>{v || '-'}</Text> 
          },
          { 
            title: '状态', 
            dataIndex: 'status', 
            key: 'status',
            render: (v) => {
              const color = v === 'done' ? 'success' : v === 'failed' ? 'error' : 'processing';
              return <Tag color={color}>{v?.toUpperCase()}</Tag>
            }
          },
          { title: '耗时', dataIndex: 'duration_ms', key: 'duration_ms', render: (v) => v ? `${(v/1000).toFixed(1)}s` : '-' },
          { title: '问题数', dataIndex: 'issues_count', key: 'issues_count', render: (v) => v ?? '-' },
          {
            title: '操作',
            key: 'op',
            width: 200,
            render: (_, r) => (
              <Space>
                {r.status === 'done' && (r.issues_count || 0) > 0 && (
                  <Button
                    size="small"
                    type="link"
                    onClick={async () => {
                      try {
                        const fx = await formatReviewAPI.autoFix(r.history_id)
                        message.success('已开始一键修改，正在生成下载链接…')
                        const poll = async () => {
                          const st = await formatReviewAPI.getFixTask(fx.fix_task_id)
                          if (st.status === 'done' && st.download_url) {
                            window.open(st.download_url, '_blank')
                            message.success('已生成下载链接（一次性有效）')
                            return
                          }
                          if (st.status === 'failed') {
                            message.error(st.error || '一键修改失败')
                            return
                          }
                          window.setTimeout(poll, 1500)
                        }
                        window.setTimeout(poll, 800)
                      } catch (e: any) {
                        message.error(toErrorMessage(e, '一键修改失败'))
                      }
                    }}
                  >
                    一键修改
                  </Button>
                )}
                <Button
                  size="small"
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={async () => {
                    try {
                      await formatReviewAPI.deleteHistory(r.history_id)
                      message.success('已删除')
                      loadHistory()
                    } catch (e: any) {
                      message.error(toErrorMessage(e, '删除失败'))
                    }
                  }}
                >
                  删除
                </Button>
              </Space>
            ),
          },
        ]}
      />
    </Card>
  )

  const rulesPane = (
    <div className="frb-rules-container">
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={10}>
          <Space direction="vertical" size={24} style={{ width: '100%' }}>
            <Card className="frb-card" title={<Space><CloudUploadOutlined /><span>上传/生成规则</span></Space>}>
              <Upload.Dragger
                className="frb-upload-dragger"
                multiple={false}
                accept=".pdf,.docx,.doc,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                beforeUpload={(f) => {
                  const ext = (f.name || '').toLowerCase()
                  const ok = ext.endsWith('.pdf') || ext.endsWith('.docx') || ext.endsWith('.doc')
                  if (!ok) {
                    message.error('仅支持 .pdf / .docx / .doc')
                    return Upload.LIST_IGNORE
                  }
                  if ((f as any).size && (f as any).size > 20 * 1024 * 1024) {
                    message.error('单文件大小不能超过 20MB')
                    return Upload.LIST_IGNORE
                  }
                  setRuleFile(f as unknown as File)
                  setRuleFileId(null)
                  setRuleGenStatus(null)
                  setRuleGenTaskId(null)
                  return false
                }}
                fileList={ruleFile ? [{ uid: 'rule', name: ruleFile.name, size: ruleFile.size, status: 'done' }] : []}
                onRemove={() => {
                  setRuleFile(null)
                  setRuleFileId(null)
                  return true
                }}
              >
                <p className="frb-upload-icon" style={{ fontSize: 32, marginBottom: 8 }}><InboxOutlined /></p>
                <p className="frb-upload-text">点击或拖拽规则文档</p>
                <p className="frb-upload-hint">支持 .pdf / .docx / .doc，≤20MB</p>
              </Upload.Dragger>
              <Button
                type="primary"
                block
                className="frb-mt-md"
                disabled={!ruleFile || !!ruleGenTaskId}
                loading={!!ruleGenTaskId}
                onClick={async () => {
                  if (!ruleFile) return
                  try {
                    const ensured = ruleFileId || (await ruleAPI.upload(ruleFile)).file_id
                    setRuleFileId(ensured)
                    const gen = await ruleAPI.generate(ensured)
                    setRuleGenTaskId(gen.task_id)
                    setRuleGenStatus('queued')
                    message.success('已开始生成规则…')
                  } catch (e: any) {
                    message.error(toErrorMessage(e, '生成失败'))
                  }
                }}
              >
                {ruleGenTaskId ? '规则生成中...' : '生成规则'}
              </Button>
              {ruleGenTaskId && <div className="frb-mt-sm"><Text type="secondary">状态：{ruleGenStatus || 'running'}</Text></div>}
            </Card>

            <Card className="frb-card" title={<Space><SettingOutlined /><span>我的规则</span></Space>}>
              {rules.length ? (
                <div style={{ display: 'grid', gap: 12, marginBottom: 12 }}>
                  {rules
                    .slice()
                    .sort((a, b) => Number(b.pinned) - Number(a.pinned))
                    .map((r) => {
                      const activeCard = manageRuleId === r.rule_id
                      const skillName = manageRuleDetail?.rule_id === r.rule_id ? (manageRuleDetail as any)?.content?.skill?.name : null
                      return (
                        <Card
                          key={r.rule_id}
                          size="small"
                          className="frb-card"
                          style={{ borderColor: activeCard ? '#1677ff' : undefined }}
                          title={
                            <Space>
                              {r.pinned && <PushpinFilled style={{ color: '#1677ff' }} />}
                              <span>{r.name}</span>
                              <Tag bordered={false}>v{r.version}</Tag>
                            </Space>
                          }
                          extra={
                            <Button
                              size="small"
                              type="link"
                              icon={<RocketOutlined />}
                              onClick={(ev) => {
                                ev.stopPropagation()
                                setSelectedRule(r.rule_id)
                                setActive('review')
                                message.success('已切换到该规则用于审查')
                              }}
                            >
                              用于审查
                            </Button>
                          }
                          onClick={() => loadRuleDetail(r.rule_id)}
                        >
                          <div style={{ color: '#64748b', fontSize: 12 }}>Skill：{skillName || '（生成后可设置英文名）'}</div>
                        </Card>
                      )
                    })}
                </div>
              ) : (
                <Empty description="暂无自定义规则" />
              )}
              <Select
                style={{ width: '100%' }}
                placeholder="选择要管理的规则"
                loading={rulesLoading}
                value={manageRuleId ?? undefined}
                onChange={(v) => loadRuleDetail(v)}
                options={rules.map((r) => ({ 
                  value: r.rule_id, 
                  label: (
                    <Space>
                      {r.pinned && <PushpinFilled style={{ color: '#1677ff' }} />}
                      <span>{r.name}</span>
                      <Tag bordered={false}>v{r.version}</Tag>
                    </Space>
                  )
                }))}
              />
              <div className="frb-toolbar">
                <Button
                  disabled={!manageRuleId}
                  icon={rules.find(x => x.rule_id === manageRuleId)?.pinned ? <PushpinFilled /> : <PushpinOutlined />}
                  onClick={async () => {
                    if (!manageRuleId) return
                    try {
                      const cur = rules.find((x) => x.rule_id === manageRuleId)
                      await ruleAPI.pin(manageRuleId, !cur?.pinned)
                      try {
                        localStorage.removeItem(rulesCacheKey)
                      } catch {}
                      await loadRules(true)
                      message.success('已更新置顶状态')
                    } catch (e: any) {
                    message.error(toErrorMessage(e, '更新失败'))
                    }
                  }}
                >
                  置顶
                </Button>
                <Button
                  disabled={!manageRuleId}
                  icon={<EditOutlined />}
                  onClick={() => {
                    const cur = rules.find((x) => x.rule_id === manageRuleId)
                    setRenameValue(cur?.name || '')
                    setRenameOpen(true)
                  }}
                >
                  重命名
                </Button>
                <Button
                  disabled={!manageRuleId}
                  icon={<SettingOutlined />}
                  onClick={() => {
                    const cur = (manageRuleDetail as any)?.content?.skill?.name
                    setSkillRenameValue(String(cur || ''))
                    setSkillRenameOpen(true)
                  }}
                >
                  设置英文名
                </Button>
                <Button
                  disabled={!manageRuleId}
                  icon={<BranchesOutlined />}
                  onClick={async () => {
                    if (!manageRuleId) return
                    try {
                      const v = await ruleAPI.versions(manageRuleId)
                      setManageRuleVersions(v.versions || [])
                      setManageVersionContent(null)
                      setManageVersionOpen(true)
                    } catch (e: any) {
                    message.error(toErrorMessage(e, '加载版本失败'))
                    }
                  }}
                >
                  版本
                </Button>
                <Button
                  disabled={!manageRuleId}
                  icon={<DownloadOutlined />}
                  onClick={() => {
                    if (!manageRuleId) return
                    window.open(ruleAPI.exportUrl(manageRuleId), '_blank')
                  }}
                >
                  导出
                </Button>
                <Button
                  disabled={!manageRuleId}
                  icon={<DownloadOutlined />}
                  onClick={() => {
                    if (!manageRuleId) return
                    window.open(ruleAPI.exportSkillUrl(manageRuleId), '_blank')
                  }}
                >
                  导出Skill
                </Button>
                <Button
                  danger
                  disabled={!manageRuleId}
                  icon={<DeleteOutlined />}
                  onClick={() => {
                    if (!manageRuleId) return
                    modal.confirm({
                      title: '删除规则',
                      content: '删除后不可恢复。若该规则已被格式审查任务引用，可能需要强制删除。',
                      okText: '删除',
                      okButtonProps: { danger: true },
                      cancelText: '取消',
                      onOk: async () => {
                        try {
                          await ruleAPI.remove(manageRuleId, false)
                          try {
                            localStorage.removeItem(rulesCacheKey)
                          } catch {}
                          await loadRules(true)
                          setManageRuleId(null)
                          setManageRuleDetail(null)
                          message.success('已删除')
                        } catch (e: any) {
                          const detail = e?.response?.data?.detail
                          if (String(detail || '').includes('referenced')) {
                            modal.confirm({
                              title: '规则已被引用',
                              content: '是否强制删除？强制删除将使历史任务中的 rule_id 失去关联。',
                              okText: '强制删除',
                              okButtonProps: { danger: true },
                              cancelText: '取消',
                              onOk: async () => {
                                await ruleAPI.remove(manageRuleId, true)
                                try {
                                  localStorage.removeItem(rulesCacheKey)
                                } catch {}
                                await loadRules(true)
                                setManageRuleId(null)
                                setManageRuleDetail(null)
                                message.success('已强制删除')
                              },
                            })
                            return
                          }
                          message.error(toErrorMessage(e, '删除失败'))
                        }
                      },
                    })
                  }}
                >
                  删除
                </Button>
              </div>
            </Card>
          </Space>
        </Col>

        <Col xs={24} lg={14}>
          <Card 
            className="frb-card" 
            title={<Space><FileTextOutlined /><span>规则内容预览</span></Space>}
            extra={
              manageRuleDetail?.content && (
                <Space>
                  <Select
                    size="small"
                    value={rulePreviewMode}
                    onChange={(v) => setRulePreviewMode(v)}
                    options={[
                      { value: 'skill', label: 'Skill' },
                      { value: 'json', label: 'JSON' },
                    ]}
                  />
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={async () => {
                      try {
                        const txt =
                          rulePreviewMode === 'skill'
                            ? String((manageRuleDetail as any)?.content?.skill?.markdown || '')
                            : JSON.stringify(manageRuleDetail.content, null, 2)
                        await navigator.clipboard.writeText(txt)
                        message.success('已复制')
                      } catch {
                        message.error('复制失败')
                      }
                    }}
                  >
                    复制
                  </Button>
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    disabled={!manageRuleId}
                    onClick={() => {
                      if (!manageRuleId) return
                      window.open(rulePreviewMode === 'skill' ? ruleAPI.exportSkillUrl(manageRuleId) : ruleAPI.exportUrl(manageRuleId), '_blank')
                    }}
                  >
                    下载
                  </Button>
                </Space>
              )
            }
          >
            {manageRuleDetail ? (
              rulePreviewMode === 'skill' ? (
                <pre className="frb-json-preview">
                  {String((manageRuleDetail as any)?.content?.skill?.markdown || '暂无 Skill 内容（请先生成规则或设置英文名）')}
                </pre>
              ) : (
                <pre className="frb-json-preview">
                  {JSON.stringify(manageRuleDetail.content ?? {}, null, 2)}
                </pre>
              )
            ) : (
              <Empty description="请选择一条规则以预览内容" />
            )}
          </Card>
        </Col>
      </Row>

      <Modal
        title="重命名规则"
        open={renameOpen}
        okText="保存"
        cancelText="取消"
        onCancel={() => setRenameOpen(false)}
        onOk={async () => {
          if (!manageRuleId) return
          const v = (renameValue || '').trim()
          if (!v) return
          try {
            await ruleAPI.rename(manageRuleId, v)
            setRenameOpen(false)
            try {
              localStorage.removeItem(rulesCacheKey)
            } catch {}
            await loadRules(true)
            await loadRuleDetail(manageRuleId)
            message.success('已重命名')
          } catch (e: any) {
            message.error(toErrorMessage(e, '重命名失败'))
          }
        }}
      >
        <Input value={renameValue} onChange={(e) => setRenameValue(e.target.value)} maxLength={30} placeholder="规则名称（≤30字符）" />
      </Modal>

      <Modal
        title="设置英文 Skill 名"
        open={skillRenameOpen}
        okText="保存"
        cancelText="取消"
        onCancel={() => setSkillRenameOpen(false)}
        onOk={async () => {
          if (!manageRuleId) return
          const v = (skillRenameValue || '').trim()
          if (!v) return
          try {
            await ruleAPI.renameSkill(manageRuleId, v)
            setSkillRenameOpen(false)
            try {
              localStorage.removeItem(rulesCacheKey)
            } catch {}
            await loadRules(true)
            await loadRuleDetail(manageRuleId)
            message.success('已更新 Skill 名')
          } catch (e: any) {
            message.error(toErrorMessage(e, '更新失败'))
          }
        }}
      >
        <Input value={skillRenameValue} onChange={(e) => setSkillRenameValue(e.target.value)} maxLength={64} placeholder="英文名（如 snda-format-review-v1）" />
      </Modal>

      <Modal title="版本管理" open={manageVersionOpen} onCancel={() => setManageVersionOpen(false)} footer={null} width={920}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          <div>
            <Table
              rowKey="version"
              pagination={false}
              dataSource={manageRuleVersions}
              size="small"
              columns={[
                { title: '版本', dataIndex: 'version', key: 'version', width: 80, render: v => <Tag>v{v}</Tag> },
                { title: '创建时间', dataIndex: 'created_at', key: 'created_at', ellipsis: true },
                {
                  title: '操作',
                  key: 'op',
                  render: (_, r) => (
                    <Space size="small">
                      <Button
                        size="small"
                        type="link"
                        disabled={!manageRuleId}
                        onClick={async () => {
                          if (!manageRuleId) return
                          try {
                            const v = await ruleAPI.version(manageRuleId, r.version)
                            setManageVersionContent(v.content)
                          } catch (e: any) {
                            message.error(toErrorMessage(e, '读取版本失败'))
                          }
                        }}
                      >
                        查看
                      </Button>
                      <Button
                        size="small"
                        type="link"
                        danger
                        disabled={!manageRuleId}
                        onClick={() => {
                          if (!manageRuleId) return
                          modal.confirm({
                            title: `回滚到 v${r.version}`,
                            content: '回滚会生成一个新版本号，并仅保留最近 5 个版本。',
                            okText: '回滚',
                            cancelText: '取消',
                            onOk: async () => {
                              await ruleAPI.rollback(manageRuleId, r.version)
                              try {
                                localStorage.removeItem(rulesCacheKey)
                              } catch {}
                              await loadRules(true)
                              await loadRuleDetail(manageRuleId)
                              const vlist = await ruleAPI.versions(manageRuleId)
                              setManageRuleVersions(vlist.versions || [])
                              message.success('已回滚')
                            },
                          })
                        }}
                      >
                        回滚
                      </Button>
                    </Space>
                  ),
                },
              ]}
            />
          </div>
          <div>
            <div style={{ color: '#64748b', marginBottom: 8, fontWeight: 500 }}>选定版本内容预览</div>
            <pre className="frb-json-preview" style={{ maxHeight: 400 }}>
              {JSON.stringify(manageVersionContent ?? {}, null, 2)}
            </pre>
          </div>
        </div>
      </Modal>
    </div>
  )

  return (
    <div className="frb-page">
      {error ? <Alert type="warning" showIcon message={error} style={{ marginBottom: 12 }} /> : null}
      {loading ? (
        <div className="frb-loading">
          <Spin size="large" tip="加载中..." />
        </div>
      ) : (
        <Tabs
          activeKey={active}
          onChange={(k) => setActive(k as any)}
          className="frb-tabs"
          items={[
            { key: 'review', label: '格式审查', children: reviewPane },
            { key: 'history', label: '审查历史', children: historyPane },
            { key: 'rules', label: '自定义规则', children: rulesPane },
          ]}
        />
      )}
    </div>
  )
}
