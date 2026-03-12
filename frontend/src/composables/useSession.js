import { reactive, readonly } from 'vue'

import sseClient from '../components/SSEClient'
import { authService, eventService } from '../services/api'
import {
  clearStoredSession,
  getStoredToken,
  getStoredUser,
  saveStoredSession,
} from '../services/sessionStorage'

const state = reactive({
  ready: false,
  token: getStoredToken(),
  user: getStoredUser(),
  unreadCount: 0,
  sseConnected: false,
  toasts: [],
  pendingAlerts: [],
})

let sessionInitialized = false
let listenersBound = false
let toastCounter = 0

function bindListeners() {
  if (listenersBound) {
    return
  }

  listenersBound = true
  sseClient.on('timer_fired', handleTimerFired)
  sseClient.on('__status__', handleSseStatus)
  window.addEventListener('session-expired', handleSessionExpired)
}

function handleSessionExpired() {
  resetSessionState()
}

function handleSseStatus(status) {
  state.sseConnected = status === 'connected'
}

function handleTimerFired(event) {
  state.unreadCount += 1
  state.pendingAlerts.push({
    eventId: event.event_id,
    timerId: event.timer_id,
    timerName: event.timer_name || '未命名定时器',
    firedAt: event.fired_at,
  })
}

function resetSessionState() {
  sseClient.disconnect()
  state.token = null
  state.user = null
  state.unreadCount = 0
  state.sseConnected = false
  state.pendingAlerts = []
}

function setSession(token, user) {
  saveStoredSession({ token, user })
  state.token = token
  state.user = user
}

export function pushToast({ tone = 'info', title, message, duration = 3200 }) {
  const id = `${Date.now()}-${toastCounter++}`
  state.toasts.push({ id, tone, title, message })

  if (duration > 0) {
    window.setTimeout(() => {
      removeToast(id)
    }, duration)
  }
}

export function removeToast(id) {
  const index = state.toasts.findIndex((toast) => toast.id === id)
  if (index >= 0) {
    state.toasts.splice(index, 1)
  }
}

export async function refreshUnreadCount() {
  if (!state.token) {
    state.unreadCount = 0
    return 0
  }

  const events = await eventService.list({ unread_only: 1 })
  state.unreadCount = events.length
  return state.unreadCount
}

export async function acknowledgePendingAlert() {
  const alert = state.pendingAlerts[0]
  if (!alert) {
    return
  }

  await eventService.ack(alert.eventId)
  state.pendingAlerts.shift()
  state.unreadCount = Math.max(0, state.unreadCount - 1)

  pushToast({
    tone: 'accent',
    title: '事件已确认',
    message: `“${alert.timerName}” 已标记为已读。`,
  })
}

export async function initializeSession() {
  bindListeners()

  if (sessionInitialized) {
    return
  }

  state.ready = false
  state.token = getStoredToken()
  state.user = getStoredUser()

  if (!state.token) {
    state.ready = true
    sessionInitialized = true
    return
  }

  try {
    const me = await authService.getMe()
    const user = {
      id: me.user_id,
      username: me.username,
    }
    setSession(state.token, user)
    await refreshUnreadCount()
    sseClient.connect()
  } catch {
    clearStoredSession()
    resetSessionState()
  } finally {
    state.ready = true
    sessionInitialized = true
  }
}

export async function loginWithPassword(username, password) {
  bindListeners()

  const response = await authService.login(username.trim(), password)
  const user = {
    id: response.user_id,
    username: response.username,
  }

  setSession(response.token, user)
  state.ready = true
  await refreshUnreadCount()
  sseClient.connect()

  return response
}

export function logout() {
  clearStoredSession()
  resetSessionState()
}

export function useSession() {
  return {
    state: readonly(state),
    initializeSession,
    loginWithPassword,
    logout,
    refreshUnreadCount,
    acknowledgePendingAlert,
    pushToast,
    removeToast,
  }
}
