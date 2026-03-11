<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { timerService, eventService } from '../services/api'
import sseClient from '../components/SSEClient'

const router = useRouter()

const timers = ref([])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const editingTimer = ref(null)
const newTimer = ref({
  name: '',
  type: 'once',
  delay_hours: 0,
  delay_minutes: 5,
  delay_seconds: 0,
  time_of_day: '00:00:00'
})
const unreadCount = ref(0)
const now = ref(Date.now())
let countdownInterval = null

// 计算倒计时
function getCountdown(nextFireAt) {
  if (!nextFireAt) return ''
  const diff = new Date(nextFireAt).getTime() - now.value
  if (diff <= 0) return '即将触发'

  const seconds = Math.floor(diff / 1000)
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours}小时${minutes}分${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`
  } else {
    return `${secs}秒`
  }
}

// 格式化下次触发时间
function formatNextFire(nextFireAt) {
  if (!nextFireAt) return ''
  return new Date(nextFireAt).toLocaleString()
}

async function loadTimers() {
  try {
    timers.value = await timerService.list()
  } catch (err) {
    console.error('加载定时器失败:', err)
  }
}

async function loadUnreadCount() {
  try {
    // 获取未读事件数量
    const events = await eventService.list({ unread_only: 1 })
    unreadCount.value = events.length
  } catch (err) {
    console.error('获取未读数量失败:', err)
  }
}

async function createTimer() {
  try {
    const data = { ...newTimer.value }
    // 将时分秒转换为秒
    if (data.type === 'once') {
      data.delay_seconds = data.delay_hours * 3600 + data.delay_minutes * 60 + data.delay_seconds
      delete data.delay_hours
      delete data.delay_minutes
      delete data.time_of_day
    }
    await timerService.create(data)
    showCreateDialog.value = false
    newTimer.value = {
      name: '',
      type: 'once',
      delay_hours: 0,
      delay_minutes: 5,
      delay_seconds: 0,
      time_of_day: '00:00:00'
    }
    loadTimers()
  } catch (err) {
    alert(err.response?.data?.error || '创建失败')
  }
}

async function updateTimer(timer) {
  try {
    const data = {
      status: timer.status
    }
    if (timer.type === 'once' && editingTimer.value.delay_seconds) {
      data.delay_seconds = editingTimer.value.delay_seconds
    }
    if (timer.type === 'daily' && editingTimer.value.time_of_day) {
      data.time_of_day = editingTimer.value.time_of_day
    }
    await timerService.update(timer.id, data)
    showEditDialog.value = false
    loadTimers()
  } catch (err) {
    alert(err.response?.data?.error || '更新失败')
  }
}

async function deleteTimer(timer) {
  if (confirm(`确定要删除定时器 "${timer.name}" 吗？`)) {
    try {
      await timerService.delete(timer.id)
      loadTimers()
    } catch (err) {
      alert(err.response?.data?.error || '删除失败')
    }
  }
}

function openCreateDialog() {
  showCreateDialog.value = true
}

function openEditDialog(timer) {
  editingTimer.value = { ...timer }
  showEditDialog.value = true
}


function goToEvents() {
  router.push('/events')
}

// 保存回调引用，用于移除
async function handleTimerFired(data) {
  alert(`定时器 "${data.timer_name}" 已触发！`)
  // 点击确定后自动标记为已读并刷新列表
  try {
    await eventService.ack(data.event_id)
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    // 刷新定时器列表以更新下次触发时间
    loadTimers()
  } catch (err) {
    console.error('标记已读失败:', err)
  }
}

onMounted(() => {
  loadTimers()
  loadUnreadCount()
  sseClient.connect()

  // 每秒更新倒计时
  countdownInterval = setInterval(() => {
    now.value = Date.now()
  }, 1000)

  // 监听 SSE 事件（保存引用以便移除）
  sseClient.on('timer_fired', handleTimerFired)
})

onUnmounted(() => {
  sseClient.off('timer_fired', handleTimerFired)  // 移除监听器
  sseClient.disconnect()
  if (countdownInterval) {
    clearInterval(countdownInterval)
  }
})
</script>

<template>
  <div class="timers-page">
    <div class="header">
      <h1>定时器</h1>
      <div class="actions">
        <div v-if="unreadCount > 0" class="unread-badge" @click="goToEvents">
          {{ unreadCount }} 条未读事件
        </div>
        <button @click="openCreateDialog">+ 新建定时器</button>
      </div>
    </div>

    <div v-if="timers.length === 0" class="empty">
      <p>暂无定时器</p>
    </div>

    <div class="timer-list">
      <div v-for="timer in timers" :key="timer.id" class="timer-item">
        <div class="timer-info">
          <h3>{{ timer.name }}</h3>
          <div class="meta">
            <span class="type">{{ timer.type }}</span>
            <span class="status" :class="timer.status">{{ timer.status }}</span>
          </div>
          <div v-if="timer.next_fire_at && timer.status === 'enabled'" class="next-fire">
            <div>下次触发: {{ formatNextFire(timer.next_fire_at) }}</div>
            <div class="countdown">倒计时: {{ getCountdown(timer.next_fire_at) }}</div>
          </div>
        </div>
        <div class="timer-actions">
          <button @click="openEditDialog(timer)">编辑</button>
          <button @click="deleteTimer(timer)" class="delete">删除</button>
        </div>
      </div>
    </div>

    <!-- 创建定时器对话框 -->
    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="showCreateDialog = false">
      <div class="dialog">
        <h2>新建定时器</h2>
        <div class="form-group">
          <label>名称</label>
          <input v-model="newTimer.name" placeholder="定时器名称" />
        </div>
        <div class="form-group">
          <label>类型</label>
          <select v-model="newTimer.type">
            <option value="once">一次性</option>
            <option value="daily">每日定时</option>
          </select>
        </div>
        <div v-if="newTimer.type === 'once'" class="form-group time-input-group">
          <label>延迟时间</label>
          <div class="time-inputs">
            <div class="time-input-item">
              <input v-model.number="newTimer.delay_hours" type="number" min="0" max="23" />
              <span>时</span>
            </div>
            <div class="time-input-item">
              <input v-model.number="newTimer.delay_minutes" type="number" min="0" max="59" />
              <span>分</span>
            </div>
            <div class="time-input-item">
              <input v-model.number="newTimer.delay_seconds" type="number" min="0" max="59" />
              <span>秒</span>
            </div>
          </div>
        </div>
        <div v-if="newTimer.type === 'daily'" class="form-group">
          <label>触发时间 (HH:MM:SS)</label>
          <input v-model="newTimer.time_of_day" type="time" step="1" />
        </div>
        <div class="dialog-actions">
          <button @click="showCreateDialog = false">取消</button>
          <button @click="createTimer">创建</button>
        </div>
      </div>
    </div>

    <!-- 编辑定时器对话框 -->
    <div v-if="showEditDialog && editingTimer" class="dialog-overlay" @click.self="showEditDialog = false">
      <div class="dialog">
        <h2>编辑定时器</h2>
        <div v-if="editingTimer.type === 'once'" class="form-group">
          <label>延迟（秒）</label>
          <input v-model.number="editingTimer.delay_seconds" type="number" min="1" max="86400" />
        </div>
        <div v-if="editingTimer.type === 'daily'" class="form-group">
          <label>触发时间 (HH:MM:SS)</label>
          <input v-model="editingTimer.time_of_day" type="time" step="1" />
        </div>
        <div class="dialog-actions">
          <button @click="showEditDialog = false">取消</button>
          <button @click="updateTimer(editingTimer)">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timers-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.unread-badge {
  background: #ff5722;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

button {
  padding: 8px 16px;
  background: #42b883;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button.delete {
  background: #f44336;
}

.timer-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.timer-item {
  display: flex;
  justify-content: space-between;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.timer-info {
  flex: 1;
}

.timer-info h3 {
  margin: 0 0 10px 0;
}

.meta {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.type, .status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.type {
  background: #e3f2fd;
  color: #1565c0;
}

.status {
  color: white;
}

.status.enabled {
  background: #4caf50;
}

.status.paused {
  background: #ff9800;
}

.status.completed {
  background: #9e9e9e;
}

.next-fire {
  margin-top: 8px;
}

.countdown {
  color: #ff5722;
  font-weight: bold;
  font-size: 14px;
  margin-top: 4px;
}

.timer-actions {
  display: flex;
  gap: 8px;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog {
  background: white;
  padding: 30px;
  border-radius: 8px;
  min-width: 400px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.empty {
  text-align: center;
  color: #999;
}

/* 时分秒选择器 */
.time-input-group label {
  display: block;
  margin-bottom: 8px;
}

.time-inputs {
  display: flex;
  gap: 10px;
  align-items: center;
}

.time-input-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.time-input-item input {
  width: 60px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.time-input-item span {
  color: #666;
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .dialog {
    background: #1a1a1a;
    color: #fff;
  }

  .dialog h2 {
    color: #fff;
  }

  .form-group label {
    color: #fff;
  }

  .form-group input,
  .form-group select {
    background: #333;
    border-color: #555;
    color: #fff;
  }

  .form-group input::placeholder {
    color: #999;
  }

  .time-input-item input {
    background: #333;
    border-color: #555;
    color: #fff;
  }

  .time-input-item span {
    color: #aaa;
  }
}
</style>