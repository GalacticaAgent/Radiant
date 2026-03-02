import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useTheme } from '../../hooks/useTheme'
import remarkGfm from 'remark-gfm'
import mermaid from 'mermaid'
import { useEffect, useMemo, useRef, useState } from 'react'
import './MarkdownRenderer.css'

interface MarkdownRendererProps {
  content: string
}

function MermaidDiagram({ code, isDark }: { code: string; isDark: boolean }) {
  const idRef = useRef(`mmd-${Math.random().toString(36).slice(2)}`)
  const [svg, setSvg] = useState<string | null>(null)

  useEffect(() => {
    let disposed = false
    mermaid.initialize({ startOnLoad: false, theme: isDark ? 'dark' : 'default' })
    mermaid
      .render(idRef.current, code)
      .then((r) => {
        if (disposed) return
        setSvg(r.svg)
      })
      .catch(() => {
        if (disposed) return
        setSvg(null)
      })
    return () => {
      disposed = true
    }
  }, [code, isDark])

  return svg ? <div dangerouslySetInnerHTML={{ __html: svg }} /> : null
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const { isDark } = useTheme()
  const gfmPlugins = useMemo(() => [remarkGfm], [])

  return (
    <div className="markdown-renderer">
      <ReactMarkdown
        remarkPlugins={gfmPlugins}
        components={{
          pre({ children }) {
            return <>{children}</>
          },
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            const language = match ? match[1] : ''
            const raw = String(children).replace(/\n$/, '')
            const rawTrimmed = raw.trim()
            const normalizedLang = language.toLowerCase()

            const looksLikeReviewMeta =
              /"strengths"\s*:/.test(raw) && /"weaknesses"\s*:/.test(raw) && /"suggestions"\s*:/.test(raw)

            if (normalizedLang === 'json') {
              const looksLikeFormatReviewMeta =
                /"issues"\s*:/.test(raw) &&
                (/"overall_grade"\s*:/.test(raw) ||
                  /"priority"\s*:/.test(raw) ||
                  (/"severity"\s*:/.test(raw) && /"position"\s*:/.test(raw) && /"description"\s*:/.test(raw)))
              if (looksLikeFormatReviewMeta || looksLikeReviewMeta) return null
            }
            if (!normalizedLang && rawTrimmed.startsWith('{') && (looksLikeReviewMeta || /"issues"\s*:/.test(raw))) {
              return null
            }

            const looksLikeMermaid =
              normalizedLang === 'mermaid' ||
              (!normalizedLang &&
                /^(graph\s+(TD|LR|RL|BT)\b|sequenceDiagram\b|flowchart\s+(TD|LR|RL|BT)\b|classDiagram\b|stateDiagram\b|erDiagram\b)/i.test(
                  rawTrimmed
                ))
            if (looksLikeMermaid) {
              return <MermaidDiagram code={raw} isDark={isDark} />
            }

            return language ? (
              <SyntaxHighlighter
                style={isDark ? vscDarkPlus : vs}
                language={language}
                PreTag="div"
              >
                {raw}
              </SyntaxHighlighter>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            )
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
