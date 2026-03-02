export interface StreamMessage {
  content: string
  done: boolean
}

export const parseStreamData = (data: string): StreamMessage | null => {
  try {
    const parsed = JSON.parse(data)
    return {
      content: parsed.content || '',
      done: parsed.done || false,
    }
  } catch {
    return null
  }
}

export const createEventSourceWithRetry = (
  url: string,
  options: {
    maxRetries?: number
    retryDelay?: number
    onMessage?: (data: StreamMessage) => void
    onError?: (error: Event) => void
    onComplete?: () => void
  } = {}
): { eventSource: EventSource; close: () => void } => {
  const { maxRetries = 3, retryDelay = 1000 } = options
  let retries = 0
  let eventSource: EventSource | null = null

  const connect = () => {
    try {
      eventSource = new EventSource(url)

      eventSource.onmessage = (event) => {
        const data = parseStreamData(event.data)
        if (data) {
          options.onMessage?.(data)
          if (data.done) {
            options.onComplete?.()
            eventSource?.close()
          }
        }
      }

      eventSource.onerror = (error) => {
        console.error('EventSource error:', error)
        eventSource?.close()

        if (retries < maxRetries) {
          retries++
          setTimeout(connect, retryDelay * Math.pow(2, retries - 1))
        } else {
          options.onError?.(error)
        }
      }
    } catch (error) {
      console.error('Failed to create EventSource:', error)
      options.onError?.(new Event('error'))
    }
  }

  connect()

  return {
    eventSource: eventSource!,
    close: () => {
      eventSource?.close()
    },
  }
}
