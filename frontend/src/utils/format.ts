export const formatDate = (date: Date | string, format: 'short' | 'long' = 'short'): string => {
  const d = typeof date === 'string' ? new Date(date) : date

  if (format === 'short') {
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    if (d.toDateString() === today.toDateString()) {
      const hours = d.getHours()
      const minutes = String(d.getMinutes()).padStart(2, '0')
      return hours + ':' + minutes
    }

    if (d.toDateString() === yesterday.toDateString()) {
      return 'Yesterday'
    }

    if (d.getFullYear() === today.getFullYear()) {
      const month = d.getMonth() + 1
      const day = d.getDate()
      return month + '/' + day
    }

    const year = d.getFullYear()
    const month = d.getMonth() + 1
    const day = d.getDate()
    return year + '/' + month + '/' + day
  }

  return d.toLocaleString()
}

export const formatTime = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return hours + ':' + minutes
}

export const formatRelativeTime = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const seconds = Math.floor((now.getTime() - d.getTime()) / 1000)

  if (seconds < 60) return 'just now'
  if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago'
  if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago'
  if (seconds < 604800) return Math.floor(seconds / 86400) + 'd ago'

  return formatDate(d, 'short')
}

export const bytesToSize = (bytes: number): string => {
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 Bytes'

  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
}

export const truncateText = (text: string, length: number = 100): string => {
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}
