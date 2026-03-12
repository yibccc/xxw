<script setup>
import { computed, onMounted, ref } from 'vue'

import PageHeader from '../components/ui/PageHeader.vue'
import { useSession } from '../composables/useSession'
import { eventService } from '../services/api'

const { refreshUnreadCount, pushToast } = useSession()
const events = ref([])
const loading = ref(false)
const unreadOnly = ref(false)

const filteredEvents = computed(() => {
  if (!unreadOnly.value) {
    return events.value
  }
  return events.value.filter((event) => !event.is_read)
})

async function loadEvents() {
  loading.value = true
  try {
    events.value = await eventService.list()
  } catch (error) {
    pushToast({ tone: 'danger', title: '加载失败', message: error.response?.data?.error || '无法获取事件列表。' })
  } finally {
    loading.value = false
  }
}

async function ackEvent(event) {
  try {
    await eventService.ack(event.id)
    event.is_read = true
    event.read_at = new Date().toISOString()
    await refreshUnreadCount()
    pushToast({ tone: 'accent', title: '已标记事件', message: `“${event.timer_name}” 的事件已标记为已读。` })
  } catch (error) {
    pushToast({ tone: 'danger', title: '操作失败', message: error.response?.data?.error || '请稍后重试。' })
  }
}

async function ackAll() {
  try {
    const response = await eventService.ackAll()
    events.value = events.value.map((event) => ({
      ...event,
      is_read: true,
      read_at: event.read_at || new Date().toISOString(),
    }))
    await refreshUnreadCount()
    pushToast({ tone: 'accent', title: '全部已读', message: response.message || '所有未读事件已完成处理。' })
  } catch (error) {
    pushToast({ tone: 'danger', title: '操作失败', message: error.response?.data?.error || '请稍后重试。' })
  }
}

onMounted(async () => {
  await loadEvents()
  await refreshUnreadCount()
})
</script>

<template>
  <div class="page-shell">
    <PageHeader
      title="事件记录"
      description="查看定时器触发历史，并管理未读事件状态。"
    >
      <template #actions>
        <button class="button ghost" type="button" @click="unreadOnly = !unreadOnly">
          {{ unreadOnly ? '显示全部' : '仅看未读' }}
        </button>
        <button class="button" type="button" @click="ackAll">全部标记已读</button>
      </template>
    </PageHeader>

    <section v-if="loading" class="panel empty-state">
      <p>正在加载事件…</p>
    </section>

    <section v-else-if="filteredEvents.length === 0" class="panel empty-state">
      <p>{{ unreadOnly ? '当前没有未读事件。' : '还没有任何事件记录。' }}</p>
    </section>

    <section v-else class="event-list">
      <article
        v-for="event in filteredEvents"
        :key="event.id"
        class="event-card"
        :data-unread="!event.is_read"
      >
        <div class="event-card__main">
          <div class="inline-meta">
            <span class="pill">{{ event.event_type === 'timer_fired' ? '触发' : event.event_type }}</span>
            <span>{{ new Date(event.created_at).toLocaleString() }}</span>
          </div>
          <h2>{{ event.timer_name || '未知定时器' }}</h2>
          <p class="event-card__copy">
            {{ event.is_read ? '该事件已处理。' : '该事件尚未处理，建议尽快确认。' }}
          </p>
        </div>
        <button
          v-if="!event.is_read"
          class="button"
          type="button"
          @click="ackEvent(event)"
        >
          标记已读
        </button>
      </article>
    </section>
  </div>
</template>

<style scoped>
.event-list {
  display: grid;
  gap: 1rem;
}

.event-card {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  padding: 1.35rem 1.5rem;
  border-radius: 24px;
  border: 1px solid var(--line);
  background: rgba(255, 250, 244, 0.88);
  box-shadow: var(--shadow-soft);
}

.event-card[data-unread='true'] {
  border-color: rgba(205, 124, 54, 0.3);
  box-shadow: 0 16px 34px rgba(205, 124, 54, 0.12);
}

.event-card__main {
  flex: 1;
}

.event-card__copy {
  margin: 0.6rem 0 0;
  color: var(--text-muted);
}

.pill {
  display: inline-flex;
  padding: 0.3rem 0.65rem;
  border-radius: 999px;
  background: rgba(83, 120, 131, 0.12);
  color: var(--ink-soft);
}

@media (max-width: 720px) {
  .event-card {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
