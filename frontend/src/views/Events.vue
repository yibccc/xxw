<script setup>
import { ref, onMounted } from 'vue'
import { eventService } from '../services/api'

const events = ref([])
const loading = ref(false)

async function loadEvents() {
  try {
    loading.value = true
    events.value = await eventService.list()
  } catch (err) {
    console.error('获取事件失败:', err)
  } finally {
    loading.value = false
  }
}

async function ackEvent(id) {
  try {
    await eventService.ack(id)
    loadEvents()
  } catch (err) {
    alert(err.response?.data?.error || '操作失败')
  }
}

async function ackAll() {
  try {
    await eventService.ackAll()
    loadEvents()
  } catch (err) {
    alert(err.response?.data?.error || '操作失败')
  }
}

onMounted(loadEvents)
</script>

<template>
  <div class="events-page">
    <div class="header">
      <h1>事件记录</h1>
      <button @click="ackAll">全部标记已读</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="events.length === 0" class="empty">
      <p>暂无事件记录</p>
    </div>

    <div class="event-list">
      <div v-for="event in events" :key="event.id" :class="['event-item', { unread: !event.is_read }]">
        <div class="event-info">
          <h3>{{ event.timer_name }}</h3>
          <div class="meta">
            <span class="type">{{ event.event_type === 'timer_fired' ? '触发' : event.event_type }}</span>
            <span class="time">{{ new Date(event.created_at).toLocaleString() }}</span>
          </div>
        </div>
        <button v-if="!event.is_read" @click="ackEvent(event.id)">标记已读</button>
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

button {
  padding: 8px 16px;
  background: #42b883;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.event-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #f9f9f9;
}

.event-item.unread {
  background: #e8f4fd;
  border-left: 4px solid #42b883;
}

.event-info h3 {
  margin: 0 0 10px 0;
}

.meta {
  display: flex;
  gap: 10px;
  color: #666;
  font-size: 14px;
}

.type {
  background: #e3f2fd;
  color: #1565c0;
  padding: 2px 8px;
  border-radius: 4px;
}

.time {
  color: #666;
}

.loading, .empty {
  text-align: center;
  color: #999;
  padding: 40px;
}
</style>