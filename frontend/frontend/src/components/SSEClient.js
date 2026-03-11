class SSEClient {
  constructor() {
    this.eventSource = null
    this.listeners = new Map()
  }

  connect() {
    if (this.eventSource) {
      this.disconnect()
    }

    const token = localStorage.getItem('token')
    if (!token) {
      console.error('No token found for SSE connection')
      return
    }

    this.eventSource = new EventSource('/api/stream', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    // 由于 EventSource 不支持自定义头，我们需要后端支持查询参数或 Cookie
    // 这里先简化实现，使用查询参数（需要后端支持）
    this.eventSource = new EventSource(`/api/stream?token=${encodeURIComponent(token)}`)

    this.eventSource.onmessage = (event) => {
      try {
        if (event.data.startsWith(':')) {
          // 注释消息，跳过
          return
        }
        const data = JSON.parse(event.data)
        this.emit(data.event, data.data)
      } catch (e) {
        console.error('Failed to parse SSE message:', e)
      }
    }

    this.eventSource.onerror = (error) => {
      console.error('SSE error:', error)
      // 5 秒后重连
      setTimeout(() => this.connect(), 5000)
    }
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
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
