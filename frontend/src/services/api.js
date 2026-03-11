import axios from 'axios'

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
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
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