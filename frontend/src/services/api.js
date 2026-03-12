import axios from 'axios'
import { clearStoredSession, getStoredToken } from './sessionStorage'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const requestUrl = error.config?.url || ''
    const isAuthRequest = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/register')
    const hasStoredToken = Boolean(getStoredToken())

    if (error.response?.status === 401 && hasStoredToken && !isAuthRequest) {
      clearStoredSession()
      window.dispatchEvent(new Event('session-expired'))
      if (window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    }
    return Promise.reject(error)
  }
)

// 导出 API 服务
export const authService = {
  register: (username, password) => api.post('/auth/register', { username, password }),
  login: (username, password) => api.post('/auth/login', { username, password }),
  getMe: () => api.get('/auth/me')
}

export const timerService = {
  list: (params) => api.get('/timers', { params }),
  get: (id) => api.get(`/timers/${id}`),
  create: (data) => api.post('/timers', data),
  update: (id, data) => api.patch(`/timers/${id}`, data),
  delete: (id) => api.delete(`/timers/${id}`)
}

export const eventService = {
  list: (params) => api.get('/events', { params }),
  ack: (id) => api.post(`/events/${id}/ack`),
  ackAll: () => api.post('/events/ack_all')
}
