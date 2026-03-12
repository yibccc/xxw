class SSEClient {
  constructor() {
    this.abortController = null
    this.reconnectTimer = null
    this.listeners = new Map()
    this.isConnected = false
    this.shouldReconnect = false
  }

  async connect() {
    if (this.abortController) return

    const token = localStorage.getItem('token')
    if (!token) {
      return
    }

    this.shouldReconnect = true
    clearTimeout(this.reconnectTimer)
    this.abortController = new AbortController()

    try {
      await this._fetchStream(token)
    } catch (error) {
      if (!this.abortController?.signal.aborted) {
        console.error('SSE connection error:', error)
        this.emit('__status__', 'error')
      }
    } finally {
      this.abortController = null
      if (this.isConnected) {
        this.isConnected = false
        this.emit('__status__', 'disconnected')
      }
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => this.connect(), 5000)
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

    this.isConnected = true
    this.emit('__status__', 'connected')

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
    const blocks = buffer.split('\n\n')
    const remainder = blocks.pop() || ''

    for (const block of blocks) {
      if (!block.trim() || block.startsWith(':')) continue

      let eventName = null
      let dataPayload = null

      for (const line of block.split('\n')) {
        if (line.startsWith('event:')) {
          eventName = line.slice(6).trim()
        }
        if (line.startsWith('data:')) {
          dataPayload = line.slice(5).trim()
        }
      }

      if (eventName && dataPayload) {
        try {
          this.emit(eventName, JSON.parse(dataPayload))
        } catch (error) {
          console.error('[SSE] Failed to parse SSE data:', error)
        }
      }
    }

    return remainder
  }

  disconnect() {
    this.shouldReconnect = false
    clearTimeout(this.reconnectTimer)

    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }
    if (this.isConnected) {
      this.isConnected = false
      this.emit('__status__', 'disconnected')
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
