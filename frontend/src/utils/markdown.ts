// Markdown processing utilities
export const escapeHtml = (text: string): string => {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  }
  return text.replace(/[&<>"']/g, (m) => map[m])
}

export const formatCodeBlock = (code: string, language: string = ''): string => {
  return `\`\`\`${language}\n${code}\n\`\`\``
}

export const isCodeBlock = (text: string): boolean => {
  return /^\s*```[\s\S]*?```\s*$/m.test(text)
}

export const extractCodeLanguage = (block: string): string => {
  const match = block.match(/^```(\w+)/)
  return match ? match[1] : ''
}

export const extractCodeContent = (block: string): string => {
  const content = block.replace(/^```[\w]*\n?/, '').replace(/\n?```$/, '')
  return content
}

// Detect if text contains markdown
export const hasMarkdown = (text: string): boolean => {
  return /[*_`\-\[\]()#+]/.test(text)
}

// Simple text formatting
export const detectFormatting = (
  text: string
): { isBold: boolean; isItalic: boolean; isCode: boolean } => {
  return {
    isBold: /\*\*.*?\*\*|\__.*?\__/.test(text),
    isItalic: /\*.*?\*|\__.*?\__/.test(text),
    isCode: /`.*?`/.test(text),
  }
}
