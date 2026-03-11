class SSEClient {
  constructor() {
    this.abortController = null
    this.listeners = new Map()
    this.isConnected = false
  }

  async connect() {
    if (this.abortController) {
      this.disconnect()
    }

    const token = localStorage.getItem('token')
    if (!token) {
      console.error('No token found for SSE connection')
      return
    }

    this.abortController = new AbortController()
    this.isConnected = true

    try {
      await this._fetchStream(token)
    } catch (error) {
      console.error('SSE connection error:', error)
      this.isConnected = false

      // 5 秒后重连
      if (this.abortController) {
        setTimeout(() => this.connect(), 5000)
      }
    }
  }

  async _fetchStream(token) {
    const response = await fetch('/api/stream', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'text/event-stream'
      },
      signal: this.abortController.signal
    })

    if (!response.ok) {
      throw new Error(`SSE connection failed: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (this.isConnected && !this.abortController.signal.aborted) {
        const { done, value } = await reader.read()

        if (done) {
          break
        }

        buffer += decoder.decode(value, { stream: true })
        buffer = this._processBuffer(buffer)
      }
    } finally {
      reader.releaseLock()
    }
  }

  _processBuffer(buffer) {
    const lines = buffer.split('\n\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.trim()) continue

      // 跳过注释行
      if (line.startsWith(':')) continue

      // 分别检查 event 和 data（不是 if-else，让两者都能被处理）
      const eventMatch = line.match(/^event:\s*(.+)$/m)
      const dataMatch = line.match(/^data:\s*(.+)$/m)

      if (eventMatch) {
        this.currentEvent = eventMatch[1]
      }

      // 独立的 if 判断，这样 data 行即使和 event 行在同一块中也能被处理
      if (dataMatch && this.currentEvent) {
        try {
          const data = JSON.parse(dataMatch[1])
          this.emit(this.currentEvent, data)
        } catch (e) {
          console.error('[SSE] Failed to parse SSE data:', e)
        }
      }
    }

    return buffer
  }

  disconnect() {
    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }
    this.isConnected = false
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return
    const callbacks = this.listeners.get(event)
    const index = callbacks.indexOf(callback)
    if (index > -1) {
      callbacks.splice(index, 1)
    }
  }

  emit(event, data) {
    if (!this.listeners.has(event)) return
    this.listeners.get(event).forEach(callback => callback(data))
  }
}

export default new SSEClient()
