import { useEffect, useMemo, useRef, useState } from 'react'
import { Modal, Avatar, Spin, Alert, Button, App, Tabs, Card, Tag, Checkbox, List, Upload, Empty, Collapse, Input, InputNumber } from 'antd'
import { FileTextOutlined, UserOutlined, DownloadOutlined, ReloadOutlined, UploadOutlined, CheckCircleOutlined, DeploymentUnitOutlined } from '@ant-design/icons'
import {
  paperAPI,
  ReviewerCandidate,
  ReviewerRecommendation,
  ReviewResponse,
  ModificationSuggestion,
  PaperPolishResponse,
  VersionListResponse,
} from '../../api/paper'
import MarkdownRenderer from '../Common/MarkdownRenderer'
import './PaperPolishModal.css'

interface PaperPolishModalProps {
  open: boolean
  paperId: string | null
  paperFilename?: string | null
  initialTab?: 'reviewers' | 'reviews' | 'suggestions' | 'polish' | 'report' | 'versions' | null
  onClose: () => void
  onReviewsGenerated: (reviews: ReviewResponse[], meta: { paperId: string; reviewerIds: string[] }) => void
  onAppendToChat: (content: string) => void
}

type BoardItem = ReviewerCandidate & { isPlaceholder?: boolean }

const makeFallbackReviewers = (): ReviewerCandidate[] => {
  return Array.from({ length: 5 }).map((_, i) => ({
    id: `dummy-reviewer-${i + 1}`,
    name: `AI Reviewer ${i + 1}`,
    affiliation: 'Virtual Lab',
    h_index: 0,
    citation_count: 0,
    paper_count: 0,
    match_score: 0,
    matched_keywords: [],
    rationale: null,
    source: 'fallback',
    external_id: `dummy-reviewer-${i + 1}`,
    top_papers: [],
  }))
}

const stripFences = (md: string) => md.replace(/```[\s\S]*?```/g, '').trim()

export default function PaperPolishModal({
  open,
  paperId,
  paperFilename,
  initialTab,
  onClose,
  onReviewsGenerated,
  onAppendToChat,
}: PaperPolishModalProps) {
  const { message } = App.useApp()
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
  const lastPaperIdRef = useRef<string | null>(null)
  const pollTimerRef = useRef<number | null>(null)
  const pollAttemptsRef = useRef(0)
  const [activeTab, setActiveTab] = useState<'reviewers' | 'reviews' | 'suggestions' | 'polish' | 'report' | 'versions'>(
    'reviewers'
  )
  const [loading, setLoading] = useState(false)
  const [reviewersLoading, setReviewersLoading] = useState(false)
  const [reviewers, setReviewers] = useState<ReviewerCandidate[]>([])
  const [selectedReviewerIds, setSelectedReviewerIds] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [candidateBuildStatus, setCandidateBuildStatus] = useState<string | null>(null)
  const [reviews, setReviews] = useState<ReviewResponse[] | null>(null)
  const [suggestions, setSuggestions] = useState<ModificationSuggestion[] | null>(null)
  const [suggestionsLoading, setSuggestionsLoading] = useState(false)
  const [selectedSuggestionTexts, setSelectedSuggestionTexts] = useState<string[]>([])
  const [polishResult, setPolishResult] = useState<PaperPolishResponse | null>(null)
  const [versions, setVersions] = useState<VersionListResponse | null>(null)
  const [versionsLoading, setVersionsLoading] = useState(false)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportMarkdown, setReportMarkdown] = useState<string | null>(null)
  const [seedModalOpen, setSeedModalOpen] = useState(false)
  const [seedQuery, setSeedQuery] = useState('computer vision')
  const [seedPerPage, setSeedPerPage] = useState(25)
  const [seedMaxAuthors, setSeedMaxAuthors] = useState(200)
  const [seeding, setSeeding] = useState(false)

  const loadCandidateReviewers = async (refresh: boolean) => {
    if (!paperId) return
    setReviewersLoading(true)
    setError(null)
    setCandidateBuildStatus(null)
    if (pollTimerRef.current) {
      window.clearTimeout(pollTimerRef.current)
      pollTimerRef.current = null
    }
    if (refresh) pollAttemptsRef.current = 0
    try {
      const res = await paperAPI.reviewerCandidates(paperId, 5, refresh)
      const candidates = res.candidates || []
      if (candidates.length) {
        setReviewers(candidates)
        const defaultSelected = candidates.slice(0, 2).map((r) => r.id)
        setSelectedReviewerIds(defaultSelected.length ? defaultSelected : ['dummy-reviewer-1'])
        if (refresh) message.success('已刷新审稿人列表')
        return
      }

      const rec = await paperAPI.reviewers(paperId, 5)
      const mapped: ReviewerCandidate[] = (rec.reviewers || []).map((r: ReviewerRecommendation) => ({
        id: r.id,
        name: r.name,
        affiliation: r.affiliation,
        h_index: r.h_index,
        citation_count: 0,
        paper_count: 0,
        match_score: r.match_count || 0,
        matched_keywords: r.matched_keywords || r.research_interests || [],
        rationale: null,
        source: 'graph',
        external_id: r.id,
        top_papers: [],
      }))
      setReviewers(mapped)
      if (!mapped.length) {
        let status: string | null = null
        try {
          const st = await paperAPI.reviewerCandidatesStatus(paperId)
          status = st?.status || null
        } catch {
          status = null
        }

        if (status === 'queued' || status === 'running') {
          setCandidateBuildStatus(status)
          setError('候选审稿人正在构建中（知识库索引/公开资料补全）。将自动重试…')
          pollAttemptsRef.current += 1
          if (pollAttemptsRef.current <= 10) {
            pollTimerRef.current = window.setTimeout(() => {
              loadCandidateReviewers(false)
            }, 3000)
          }
        } else {
          setError('未能获取候选审稿人信息（公开资料检索为空）。可稍后重试或稍后再刷新一次。')
        }
      } else if (refresh) {
        message.success('已刷新审稿人列表（回退到图谱推荐）')
      }
      const defaultSelected = mapped.slice(0, 2).map((x) => x.id)
      setSelectedReviewerIds(defaultSelected.length ? defaultSelected : ['dummy-reviewer-1'])
    } catch (e: any) {
      const msg = String(e?.message || '').toLowerCase()
      const code = e?.code
      if (code === 'ERR_CANCELED' || code === 'ERR_ABORTED' || msg.includes('canceled') || msg.includes('aborted')) {
        return
      }
      const isTimeout = code === 'ECONNABORTED' || msg.includes('timeout')
      if (isTimeout) {
        setCandidateBuildStatus('running')
        setError('候选审稿人获取超时（网络/外部检索较慢）。将自动重试…')
        pollAttemptsRef.current += 1
        if (pollAttemptsRef.current <= 10) {
          pollTimerRef.current = window.setTimeout(() => {
            loadCandidateReviewers(false)
          }, 3000)
        }
        return
      }
      setReviewers([])
      setSelectedReviewerIds(['dummy-reviewer-1'])
      setError(e?.response?.data?.detail || e?.message || '加载审稿人失败，已切换到默认审稿人')
    } finally {
      setReviewersLoading(false)
    }
  }

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) {
        window.clearTimeout(pollTimerRef.current)
        pollTimerRef.current = null
      }
    }
  }, [])

  const boardItems: BoardItem[] = useMemo(() => {
    const list = reviewers.length ? reviewers : []
    const filled: BoardItem[] = [...list]
    while (filled.length < 5) {
      const fallback = makeFallbackReviewers()[filled.length]
      filled.push({ ...fallback, isPlaceholder: true })
    }
    return filled.slice(0, 5)
  }, [reviewers])

  useEffect(() => {
    if (!open || !paperId) return
    setActiveTab(initialTab || 'reviewers')
    if (lastPaperIdRef.current !== paperId) {
      lastPaperIdRef.current = paperId
      setError(null)
      setReviewers([])
      setSelectedReviewerIds([])
      setReviews(null)
      setVersions(null)
      loadCandidateReviewers(false)
      return
    }
    if (!reviewers.length) {
      loadCandidateReviewers(false)
    }
  }, [open, paperId, initialTab])

  const loadReviews = async () => {
    if (!paperId) return
    try {
      const res = await paperAPI.reviews(paperId)
      setReviews(res.reviews || [])
    } catch {
    }
  }

  useEffect(() => {
    if (!open) {
      setLoading(false)
      setError(null)
      setReviewersLoading(false)
      setSuggestions(null)
      setSelectedSuggestionTexts([])
      setPolishResult(null)
      setVersionsLoading(false)
      setReportMarkdown(null)
      setReportLoading(false)
    }
  }, [open])

  const toggleSelect = (id: string) => {
    setSelectedReviewerIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id)
      return [...prev, id]
    })
  }

  const startReview = async () => {
    if (!paperId) return
    const reviewerIds = selectedReviewerIds.length ? selectedReviewerIds : ['dummy-reviewer-1']
    const hasRealReviewer = reviewerIds.some((id) => !String(id).startsWith('dummy-reviewer-'))
    if ((candidateBuildStatus === 'queued' || candidateBuildStatus === 'running') && !hasRealReviewer) {
      message.info('候选审稿人正在构建中，请稍后再生成审稿（避免使用占位审稿人）。')
      return
    }
    setLoading(true)
    try {
      const res = await paperAPI.generateReviews(paperId, reviewerIds)
      message.success('审稿完成，结果已输出到聊天')
      setReviews(res.reviews)
      setActiveTab('reviews')
      onReviewsGenerated(res.reviews, { paperId, reviewerIds })
      loadVersions(false)
    } catch (e: any) {
      message.error(toErrorMessage(e, '生成审稿失败'))
    } finally {
      setLoading(false)
    }
  }

  const startSeed = async () => {
    const q = seedQuery.trim()
    if (!q) {
      message.warning('请输入领域关键词（建议英文）')
      return
    }
    setSeeding(true)
    try {
      await paperAPI.seedDomainExperts({ query: q, per_page: seedPerPage, max_authors: seedMaxAuthors })
      message.success('已投递专家库预热任务')
      setSeedModalOpen(false)
      setCandidateBuildStatus('running')
      pollAttemptsRef.current = 0
      if (pollTimerRef.current) {
        window.clearTimeout(pollTimerRef.current)
        pollTimerRef.current = null
      }
      pollTimerRef.current = window.setTimeout(() => {
        loadCandidateReviewers(false)
      }, 1200)
    } catch (e: any) {
      message.error(toErrorMessage(e, '投递任务失败'))
    } finally {
      setSeeding(false)
    }
  }

  const generateSuggestions = async () => {
    if (!paperId) return
    setSuggestionsLoading(true)
    try {
      const res = await paperAPI.suggestions(paperId)
      setSuggestions(res.suggestions)
      const defaultSelected = (res.suggestions || []).slice(0, 10).map((s) => `[${s.priority}] ${s.section}: ${s.suggestion}`)
      setSelectedSuggestionTexts(defaultSelected)
      setActiveTab('suggestions')
      onAppendToChat(`已生成修改建议（${res.suggestions.length} 条）。可在弹窗中勾选后点击“一键润色摘要+diff”。`)
    } catch (e: any) {
      message.error(toErrorMessage(e, '生成修改建议失败'))
    } finally {
      setSuggestionsLoading(false)
    }
  }

  const toggleSuggestion = (text: string, checked: boolean) => {
    setSelectedSuggestionTexts((prev) => {
      if (checked) return prev.includes(text) ? prev : [...prev, text]
      return prev.filter((x) => x !== text)
    })
  }

  const applyPolish = async () => {
    if (!paperId) return
    setLoading(true)
    try {
      const selected = selectedSuggestionTexts.length
        ? selectedSuggestionTexts
        : (suggestions || []).map((s) => `[${s.priority}] ${s.section}: ${s.suggestion}`)
      const res = await paperAPI.polish(paperId, { mode: 'abstract_only', selected_suggestions: selected })
      setPolishResult(res)
      setActiveTab('polish')
      onAppendToChat(
        `已生成润色摘要与 diff。\n\n**Polished Abstract**\n\n${res.polished_abstract}\n\n**Diff**\n\n\`\`\`\n${res.diff || ''}\n\`\`\`\n`
      )
      message.success('已生成润色摘要与 diff')
    } catch (e: any) {
      message.error(toErrorMessage(e, '润色失败'))
    } finally {
      setLoading(false)
    }
  }

  const downloadReport = async () => {
    if (!paperId) return
    setReportLoading(true)
    try {
      const res = await paperAPI.report(paperId)
      setReportMarkdown(res.markdown)
      const blob = new Blob([res.markdown], { type: 'text/markdown;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `review-report-${paperId}.md`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
      onAppendToChat(`审稿报告已生成并开始下载：review-report-${paperId}.md`)
      message.success('已下载审稿报告')
      setActiveTab('report')
    } catch (e: any) {
      message.error(toErrorMessage(e, '下载报告失败'))
    } finally {
      setReportLoading(false)
    }
  }

  const loadVersions = async (switchTab: boolean = true) => {
    if (!paperId) return
    setVersionsLoading(true)
    try {
      const res = await paperAPI.versions(paperId)
      setVersions(res)
      if (switchTab) setActiveTab('versions')
    } catch (e: any) {
      message.error(toErrorMessage(e, '加载版本列表失败'))
    } finally {
      setVersionsLoading(false)
    }
  }

  const uploadVersionRequest = async (options: any) => {
    const { file, onSuccess, onError } = options
    if (!paperId) return
    try {
      await paperAPI.uploadVersion(paperId, file as File)
      message.success('已上传新版本')
      onAppendToChat(`已上传新版本：${(file as File).name}`)
      onSuccess?.(true)
      await loadVersions()
    } catch (e: any) {
      message.error(toErrorMessage(e, '上传新版本失败'))
      onError?.(e)
    }
  }

  const reviewContentHasSections = (content?: string | null) => {
    if (!content) return false
    return /(优点|缺点|建议|Strengths|Weaknesses|Suggestions|评分|Rating)/i.test(content)
  }

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      centered
      width={880}
      className="paper-polish-modal"
    >
      <div className="paper-polish-modal-header">
        <div className="paper-polish-modal-title-row">
          <div className="paper-polish-modal-title">
            <h2>模拟审稿</h2>
            <div className="paper-polish-modal-subtitle">
              <FileTextOutlined />
              <span>{paperFilename || paperId || 'Paper'}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="paper-polish-modal-body">
        {error ? (
          <Alert type="warning" showIcon message={error} style={{ marginBottom: 12 }} />
        ) : null}

        <Tabs
          className="paper-polish-tabs"
          activeKey={activeTab}
          onChange={(k) => {
            const next = k as any
            setActiveTab(next)
            if (next === 'reviews' && !reviews?.length) {
              loadReviews()
            }
            if (next === 'versions' && !versions?.versions?.length) {
              loadVersions(true)
            }
          }}
          items={[
            {
              key: 'reviewers',
              label: '审稿人',
              children: reviewersLoading ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: 24 }}>
                  <Spin />
                </div>
              ) : (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12, gap: 10, flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                      <Button icon={<ReloadOutlined />} onClick={() => loadCandidateReviewers(true)} loading={reviewersLoading} disabled={!paperId}>
                        刷新审稿人
                      </Button>
                      <Button icon={<DeploymentUnitOutlined />} onClick={() => setSeedModalOpen(true)} disabled={!paperId}>
                        预热专家库
                      </Button>
                    </div>
                  </div>
                  {candidateBuildStatus ? (
                    <Alert
                      type="info"
                      showIcon
                      message={candidateBuildStatus === 'running' ? '候选审稿人构建中…' : '候选审稿人排队中…'}
                      style={{ marginBottom: 12 }}
                    />
                  ) : null}
                  <div className="reviewer-board">
                    {boardItems.map((r) => {
                      const selected = selectedReviewerIds.includes(r.id)
                      const keywords = (r.matched_keywords || []).slice(0, 4)
                      const topPapers = (r.top_papers || []).slice(0, 2).filter((p) => p.title)
                      const sourceLabel =
                        r.source === 'semantic_scholar'
                          ? 'Semantic Scholar'
                          : r.source === 'openalex'
                            ? 'OpenAlex'
                            : r.source === 'kb'
                              ? '知识库'
                              : r.source === 'graph'
                                ? '图谱'
                                : r.source || 'Reviewer'
                      return (
                        <div
                          key={r.id}
                          className={`reviewer-card ${selected ? 'selected' : ''}`}
                          onClick={() => toggleSelect(r.id)}
                          role="button"
                          tabIndex={0}
                        >
                          <div className="reviewer-card-top">
                            <div className="reviewer-card-profile">
                              <Avatar size={40} icon={<UserOutlined />} />
                              <div style={{ minWidth: 0 }}>
                                <div className="reviewer-card-name">{r.name}</div>
                                <div className="reviewer-card-aff">{r.affiliation}</div>
                              </div>
                            </div>
                            <div className="reviewer-card-metrics">
                              <span className={`metric-pill ${selected ? 'strong' : ''}`}>H-index {r.h_index}</span>
                              <span className="metric-pill">Score {r.match_score}</span>
                            </div>
                          </div>
                          <div className="reviewer-card-tags">
                            <span className="tag-chip">{sourceLabel}</span>
                            {keywords.length
                              ? keywords.map((k) => (
                                  <span key={k} className="tag-chip">
                                    {k}
                                  </span>
                                ))
                              : null}
                            {r.rationale ? <span className="tag-chip">{r.rationale}</span> : null}
                          </div>
                          {topPapers.length ? (
                            <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                              {topPapers.map((p, idx) => (
                                <div
                                  key={`${p.paper_id || p.title || 'paper'}-${idx}`}
                                  style={{
                                    fontSize: 12,
                                    color: 'rgba(30, 41, 59, 0.72)',
                                    borderLeft: '2px solid rgba(77, 107, 254, 0.35)',
                                    paddingLeft: 8,
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                  }}
                                  title={p.title || ''}
                                >
                                  {p.year ? `${p.year} · ` : ''}
                                  {p.title}
                                </div>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      )
                    })}
                  </div>
                </div>
              ),
            },
            {
              key: 'reviews',
              label: `审稿结果${reviews?.length ? ` (${reviews.length})` : ''}`,
              children: reviews?.length ? (
                <Collapse
                  items={reviews.map((r, idx) => {
                    const title = r.reviewer_name || r.reviewer_id || `Reviewer ${idx + 1}`
                    const parsedRating = (() => {
                      if (r.rating !== null && r.rating !== undefined) return r.rating
                      const m =
                        /Rating\s*[:：]?\s*(\d{1,2})/i.exec(r.review_content || '') ||
                        /评分\s*[:：]?\s*(\d{1,2})/i.exec(r.review_content || '')
                      return m ? Number(m[1]) : null
                    })()
                    const parsedConfidence = (() => {
                      if (r.confidence) return r.confidence
                      const m =
                        /Confidence\s*[:：]?\s*([A-Za-z\u4e00-\u9fa5]+)/i.exec(r.review_content || '') ||
                        /置信度\s*[:：]?\s*([A-Za-z\u4e00-\u9fa5]+)/i.exec(r.review_content || '')
                      return m ? m[1] : null
                    })()
                    const ratingText = parsedRating !== null && parsedRating !== undefined ? `Rating ${parsedRating}/10` : 'Rating -'
                    const confidenceText = parsedConfidence ? `Confidence ${parsedConfidence}` : 'Confidence -'
                    return {
                      key: r.id || String(idx),
                      label: (
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                          <div style={{ fontWeight: 800, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {title}
                          </div>
                          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            <Tag color="blue">{ratingText}</Tag>
                            <Tag color="purple">{confidenceText}</Tag>
                          </div>
                        </div>
                      ),
                      children: (
                        <div>
                          <MarkdownRenderer content={stripFences(r.review_content || '')} />
                          {!reviewContentHasSections(r.review_content) &&
                          (r.strengths?.length || r.weaknesses?.length || r.suggestions?.length) ? (
                            <div style={{ marginTop: 12 }}>
                              {r.strengths?.length ? (
                                <div style={{ marginBottom: 10 }}>
                                  <div className="polish-block-title">Strengths</div>
                                  <List size="small" dataSource={r.strengths} renderItem={(t) => <List.Item>{t}</List.Item>} />
                                </div>
                              ) : null}
                              {r.weaknesses?.length ? (
                                <div style={{ marginBottom: 10 }}>
                                  <div className="polish-block-title">Weaknesses</div>
                                  <List size="small" dataSource={r.weaknesses} renderItem={(t) => <List.Item>{t}</List.Item>} />
                                </div>
                              ) : null}
                              {r.suggestions?.length ? (
                                <div>
                                  <div className="polish-block-title">Suggestions</div>
                                  <List size="small" dataSource={r.suggestions} renderItem={(t) => <List.Item>{t}</List.Item>} />
                                </div>
                              ) : null}
                            </div>
                          ) : null}
                        </div>
                      ),
                    }
                  })}
                />
              ) : (
                <Empty description="尚未生成审稿结果" />
              ),
            },
            {
              key: 'suggestions',
              label: `修改建议${suggestions?.length ? ` (${suggestions.length})` : ''}`,
              children: (
                <Card className="panel-card">
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
                    <Button type="primary" icon={<ReloadOutlined />} onClick={generateSuggestions} loading={suggestionsLoading} disabled={!paperId}>
                      生成修改建议
                    </Button>
                    <Button onClick={() => setSelectedSuggestionTexts([])} disabled={!suggestions?.length}>
                      清空选择
                    </Button>
                    <Button
                      type="primary"
                      icon={<CheckCircleOutlined />}
                      onClick={applyPolish}
                      loading={loading}
                      disabled={!paperId || !(suggestions?.length || selectedSuggestionTexts.length)}
                    >
                      一键润色摘要 + diff
                    </Button>
                  </div>

                  {suggestionsLoading ? (
                    <div style={{ display: 'flex', justifyContent: 'center', padding: 16 }}>
                      <Spin />
                    </div>
                  ) : suggestions?.length ? (
                    <List
                      dataSource={suggestions}
                      renderItem={(s) => {
                        const text = `[${s.priority}] ${s.section}: ${s.suggestion}`
                        const checked = selectedSuggestionTexts.includes(text)
                        const color = s.priority === '高' ? 'red' : s.priority === '低' ? 'default' : 'orange'
                        return (
                          <List.Item>
                            <Checkbox checked={checked} onChange={(e) => toggleSuggestion(text, e.target.checked)}>
                              <Tag color={color} style={{ marginRight: 8 }}>
                                {s.priority}
                              </Tag>
                              <span style={{ fontWeight: 700, marginRight: 8 }}>{s.section}</span>
                              <span>{s.suggestion}</span>
                            </Checkbox>
                          </List.Item>
                        )
                      }}
                    />
                  ) : (
                    <Alert type="info" showIcon message="点击“生成修改建议”从审稿意见中提炼可执行修改点。" />
                  )}
                </Card>
              ),
            },
            {
              key: 'polish',
              label: '润色摘要',
              children: polishResult ? (
                <Card className="panel-card">
                  <div className="polish-grid">
                    <div>
                      <div className="polish-block-title">Original Abstract</div>
                      <div style={{ color: 'rgba(30, 41, 59, 0.8)', whiteSpace: 'pre-wrap' }}>{polishResult.original_abstract}</div>
                    </div>
                    <div>
                      <div className="polish-block-title">Polished Abstract</div>
                      <div style={{ color: 'rgba(30, 41, 59, 0.85)', whiteSpace: 'pre-wrap' }}>{polishResult.polished_abstract}</div>
                    </div>
                  </div>
                  <div className="polish-block-title" style={{ marginTop: 12 }}>
                    Diff
                  </div>
                  <div className="diff-box">{polishResult.diff || '(empty diff)'}</div>
                </Card>
              ) : (
                <Empty description="先在“修改建议”里生成建议，再一键润色摘要" />
              ),
            },
            {
              key: 'report',
              label: '报告下载',
              children: (
                <Card className="panel-card">
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
                    <Button type="primary" icon={<DownloadOutlined />} onClick={downloadReport} loading={reportLoading} disabled={!paperId}>
                      下载审稿报告
                    </Button>
                  </div>
                  {reportMarkdown ? <MarkdownRenderer content={stripFences(reportMarkdown)} /> : <Alert type="info" showIcon message="点击按钮生成并下载 Markdown 报告。" />}
                </Card>
              ),
            },
            {
              key: 'versions',
              label: '版本管理',
              children: (
                <Card className="panel-card">
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
                    <Button icon={<ReloadOutlined />} onClick={() => loadVersions(true)} loading={versionsLoading} disabled={!paperId}>
                      刷新版本列表
                    </Button>
                    <Upload multiple={false} showUploadList={false} customRequest={uploadVersionRequest} disabled={!paperId}>
                      <Button icon={<UploadOutlined />} disabled={!paperId}>
                        上传新版本 PDF
                      </Button>
                    </Upload>
                  </div>
                  {versionsLoading ? (
                    <div style={{ display: 'flex', justifyContent: 'center', padding: 16 }}>
                      <Spin />
                    </div>
                  ) : versions?.versions?.length ? (
                    <List
                      dataSource={versions.versions}
                      renderItem={(v) => (
                        <List.Item>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                            <div style={{ fontWeight: 800 }}>
                              v{v.version} · {v.title || v.filename}
                            </div>
                            <div style={{ color: 'rgba(30, 41, 59, 0.6)' }}>{v.created_at}</div>
                          </div>
                        </List.Item>
                      )}
                    />
                  ) : (
                    <Alert type="info" showIcon message="暂无版本历史。上传新版本后这里会显示列表。" />
                  )}
                </Card>
              ),
            },
          ]}
        />
      </div>

      <div className="paper-polish-modal-footer">
        {activeTab === 'reviewers' ? (
          <Button
            type="primary"
            className="start-review-btn"
            onClick={startReview}
            loading={loading}
            disabled={!paperId || reviewersLoading || loading}
          >
            开始审稿
          </Button>
        ) : (
          <Button onClick={onClose} className="start-review-btn">
            关闭
          </Button>
        )}
      </div>

      <Modal
        open={seedModalOpen}
        onCancel={() => setSeedModalOpen(false)}
        onOk={startSeed}
        confirmLoading={seeding}
        okText="开始预热"
        cancelText="取消"
        centered
        title="预热专家库（OpenAlex）"
        destroyOnHidden
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ color: 'rgba(30, 41, 59, 0.7)' }}>建议使用英文领域词；任务会异步写入知识库，稍后刷新即可命中。</div>
          <Input value={seedQuery} onChange={(e) => setSeedQuery(e.target.value)} placeholder="例如: computer vision / anomaly detection" />
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {['computer vision', 'natural language processing', 'machine learning', 'anomaly detection', 'time series', 'multimodal learning'].map(
              (x) => (
                <Button key={x} size="small" onClick={() => setSeedQuery(x)}>
                  {x}
                </Button>
              )
            )}
          </div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ width: 120, color: 'rgba(30, 41, 59, 0.7)' }}>每次检索条数</div>
            <InputNumber min={1} max={25} value={seedPerPage} onChange={(v) => setSeedPerPage(Number(v || 25))} />
          </div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ width: 120, color: 'rgba(30, 41, 59, 0.7)' }}>最多新增作者</div>
            <InputNumber min={1} max={2000} value={seedMaxAuthors} onChange={(v) => setSeedMaxAuthors(Number(v || 200))} />
          </div>
        </div>
      </Modal>
    </Modal>
  )
}
