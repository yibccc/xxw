<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { eventService } from '../services/api'
import sseClient from '../components/SSEClient'

const router = useRouter()

const events = ref([])
const unreadOnly = ref(true)
const loading = ref(false)

async function loadEvents() {
  loading.value = true
  try {
    events.value = await eventService.list({
      unread_only: unreadOnly.value ? 1 : 0,
      limit: 50
    })
  } catch (err) {
    console.error('加载事件失败:', err)
  } finally {
    loading.value = false
  }
}

async function ackEvent(event) {
  try {
    await eventService.ack(event.id)
    loadEvents()
  } catch (err) {
    alert(err.response?.data?.error || '操作失败')
  }
}

async function ackAllEvents() {
  try {
    await eventService.ackAll()
    loadEvents()
  } catch (err) {
    alert(err.response?.data?.error || '操作失败')
  }
}

function goBack() {
  router.push('/timers')
}

function refresh() {
  loadEvents()
}

onMounted(() => {
  loadEvents()

  // 监听 SSE 事件
  sseClient.on('timer_fired', (data) => {
    loadEvents()
  })
})

onUnmounted(() => {
  // SSE disconnect handled by Timers page
})
</script>

<template>
  <div class="events-page">
    <div class="header">
      <h1>事件中心</h1>
      <div class="actions">
        <label class="toggle">
          <input v-model="unreadOnly" type="checkbox" @change="loadEvents" />
          <span>只显示未读</span>
        </label>
        <button @click="refresh">刷新</button>
        <button v-if="!unreadOnly && events.length > 0" @click="ackAllEvents">
          全部已读
        </button>
        <button @click="goBack">返回</button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="events.length === 0" class="empty">
      <p v-if="unreadOnly">暂无未读事件</p>
      <p v-else>暂无事件</p>
    </div>

    <div v-else class="event-list">
      <div v-for="event in events" :key="event.id" class="event-item">
        <div class="event-header">
          <h3>定时器触发</h3>
          <span class="time">{{ new Date(event.fired_at).toLocaleString() }}</span>
        </div>
        <div class="event-content">
          <p v-if="event.read_at">
            <span class="read-badge">已读</span>
            {{ new Date(event.read_at).toLocaleString() }}
          </p>
          <p v-else>
            <span class="unread-badge">未读</span>
          </p>
        </div>
        <div v-if="!event.read_at" class="event-actions">
          <button @click="ackEvent(event)">标记已读</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.events-page {
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

.toggle {
  display: flex;
  align-items: center;
  gap: 5px;
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

button:disabled {
  background: #ccc;
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.event-item {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.event-header h3 {
  margin: 0;
}

.time {
  color: #666;
  font-size: 14px;
}

.event-content p {
  margin: 10px 0;
}

.read-badge {
  background: #4caf50;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.unread-badge {
  background: #ff5722;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.event-actions {
  margin-top: 15px;
}

.loading, .empty {
  text-align: center;
  color: #999;
  padding: 40px;
}
</style>
