<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import BaseModal from '../components/ui/BaseModal.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import { useSession } from '../composables/useSession'
import { timerService } from '../services/api'
import { getCountdownLabel, getExpiredEnabledTimerIds } from './timerState'

const router = useRouter()
const { pushToast } = useSession()

const timers = ref([])
const loading = ref(false)
const createOpen = ref(false)
const editOpen = ref(false)
const deleteTarget = ref(null)
const editForm = ref(null)
const now = ref(Date.now())
let countdownInterval = null
let refreshingExpiredTimers = false
const refreshedExpiredTimerIds = new Set()

const createForm = ref(createDefaultTimerForm())

function createDefaultTimerForm() {
  return {
    name: '',
    type: 'once',
    delay_hours: 0,
    delay_minutes: 5,
    delay_seconds: 0,
    time_of_day: '09:00:00',
  }
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString() : '未安排'
}

function formatType(type) {
  return type === 'daily' ? '每日定时' : '一次性'
}

function formatStatus(status) {
  if (status === 'enabled') return '已启用'
  if (status === 'completed') return '已完成'
  if (status === 'deleted') return '已删除'
  return status
}

function summarizeTimer(timer) {
  if (timer.type === 'daily') {
    return `每天 ${timer.time_of_day} 触发`
  }
  return `延迟 ${timer.delay_seconds} 秒后触发`
}

function toCreatePayload(form) {
  const payload = {
    name: form.name.trim(),
    type: form.type,
  }

  if (payload.type === 'once') {
    payload.delay_seconds =
      Number(form.delay_hours || 0) * 3600 +
      Number(form.delay_minutes || 0) * 60 +
      Number(form.delay_seconds || 0)
  } else {
    payload.time_of_day = form.time_of_day
  }

  return payload
}

function validateCreatePayload(payload) {
  if (!payload.name) {
    return '请输入定时器名称'
  }

  if (payload.type === 'once' && (payload.delay_seconds < 1 || payload.delay_seconds > 86400)) {
    return '一次性定时器的延迟必须在 1 到 86400 秒之间'
  }

  if (payload.type === 'daily' && !payload.time_of_day) {
    return '请选择每日触发时间'
  }

  return ''
}

async function loadTimers({ background = false } = {}) {
  if (!background) {
    loading.value = true
  }
  try {
    timers.value = await timerService.list()
  } catch (error) {
    pushToast({ tone: 'danger', title: '加载失败', message: error.response?.data?.error || '无法获取定时器列表。' })
  } finally {
    if (!background) {
      loading.value = false
    }
  }
}

async function refreshExpiredTimers(currentNow) {
  if (refreshingExpiredTimers) {
    return
  }

  const expiredIds = getExpiredEnabledTimerIds(timers.value, currentNow).filter(
    (id) => !refreshedExpiredTimerIds.has(id),
  )

  if (expiredIds.length === 0) {
    return
  }

  expiredIds.forEach((id) => refreshedExpiredTimerIds.add(id))
  refreshingExpiredTimers = true

  try {
    await loadTimers({ background: true })
  } finally {
    refreshingExpiredTimers = false
  }
}

function openCreateModal() {
  createForm.value = createDefaultTimerForm()
  createOpen.value = true
}

async function submitCreate() {
  const payload = toCreatePayload(createForm.value)
  const validationError = validateCreatePayload(payload)
  if (validationError) {
    pushToast({ tone: 'danger', title: '创建失败', message: validationError })
    return
  }

  try {
    await timerService.create(payload)
    createOpen.value = false
    await loadTimers()
    pushToast({ tone: 'accent', title: '已创建定时器', message: `“${payload.name}” 已加入调度。` })
  } catch (error) {
    pushToast({ tone: 'danger', title: '创建失败', message: error.response?.data?.error || '请稍后重试。' })
  }
}

function openEditModal(timer) {
  editForm.value = {
    id: timer.id,
    name: timer.name,
    type: timer.type,
    delay_seconds: timer.delay_seconds ?? 300,
    time_of_day: timer.time_of_day ?? '09:00:00',
  }
  editOpen.value = true
}

async function submitEdit() {
  if (!editForm.value) return

  const payload = {}
  if (editForm.value.type === 'once') {
    payload.delay_seconds = Number(editForm.value.delay_seconds)
  } else {
    payload.time_of_day = editForm.value.time_of_day
  }

  try {
    await timerService.update(editForm.value.id, payload)
    editOpen.value = false
    await loadTimers()
    pushToast({ tone: 'accent', title: '已更新定时器', message: `“${editForm.value.name}” 的触发设置已更新。` })
  } catch (error) {
    pushToast({ tone: 'danger', title: '更新失败', message: error.response?.data?.error || '请稍后重试。' })
  }
}

function requestDelete(timer) {
  deleteTarget.value = timer
}

async function confirmDelete() {
  if (!deleteTarget.value) return

  try {
    await timerService.delete(deleteTarget.value.id)
    pushToast({ tone: 'accent', title: '已删除定时器', message: `“${deleteTarget.value.name}” 已移出列表。` })
    deleteTarget.value = null
    await loadTimers()
  } catch (error) {
    pushToast({ tone: 'danger', title: '删除失败', message: error.response?.data?.error || '请稍后重试。' })
  }
}

const activeTimers = computed(() => timers.value.filter((timer) => timer.status === 'enabled').length)

onMounted(() => {
  loadTimers()
  countdownInterval = window.setInterval(() => {
    now.value = Date.now()
    refreshExpiredTimers(now.value)
  }, 1000)
})

onUnmounted(() => {
  if (countdownInterval) {
    clearInterval(countdownInterval)
  }
})
</script>

<template>
  <div class="page-shell">
    <PageHeader
      title="定时器"
      :description="`当前共有 ${timers.length} 个定时器，其中 ${activeTimers} 个正在等待触发。`"
    >
      <template #actions>
        <button class="button ghost" type="button" @click="router.push('/events')">查看事件</button>
        <button class="button" type="button" @click="openCreateModal">新建定时器</button>
      </template>
    </PageHeader>

    <section v-if="loading" class="panel empty-state">
      <p>正在加载定时器…</p>
    </section>

    <section v-else-if="timers.length === 0" class="panel empty-state">
      <p>还没有定时器。先创建一个，之后你会在事件页收到触发记录。</p>
      <button class="button" type="button" @click="openCreateModal">立即创建</button>
    </section>

    <section v-else class="timer-grid">
      <article v-for="timer in timers" :key="timer.id" class="timer-card">
        <div class="timer-card__main">
          <div class="timer-card__title-row">
            <h2>{{ timer.name }}</h2>
            <span class="status-badge" :data-status="timer.status">{{ formatStatus(timer.status) }}</span>
          </div>
          <div class="inline-meta">
            <span class="pill">{{ formatType(timer.type) }}</span>
            <span>{{ summarizeTimer(timer) }}</span>
          </div>
          <div class="timer-card__timing">
            <div>
              <span class="label">下次触发</span>
              <strong>{{ formatDateTime(timer.next_fire_at) }}</strong>
            </div>
            <div>
              <span class="label">倒计时</span>
              <strong>{{ getCountdownLabel(timer, now) }}</strong>
            </div>
          </div>
        </div>
        <div class="timer-card__actions">
          <button class="button ghost" type="button" @click="openEditModal(timer)">编辑</button>
          <button class="button danger" type="button" @click="requestDelete(timer)">删除</button>
        </div>
      </article>
    </section>

    <BaseModal
      :open="createOpen"
      title="新建定时器"
      description="支持一次性延迟触发和每日固定时间触发。"
      @close="createOpen = false"
    >
      <div class="stack-lg">
        <label class="field">
          <span>名称</span>
          <input v-model="createForm.name" placeholder="例如：每日站会提醒" />
        </label>
        <label class="field">
          <span>类型</span>
          <select v-model="createForm.type">
            <option value="once">一次性</option>
            <option value="daily">每日定时</option>
          </select>
        </label>

        <div v-if="createForm.type === 'once'" class="field">
          <span>延迟时间</span>
          <div class="time-grid">
            <label class="field">
              <span>小时</span>
              <input v-model.number="createForm.delay_hours" type="number" min="0" max="23" />
            </label>
            <label class="field">
              <span>分钟</span>
              <input v-model.number="createForm.delay_minutes" type="number" min="0" max="59" />
            </label>
            <label class="field">
              <span>秒</span>
              <input v-model.number="createForm.delay_seconds" type="number" min="0" max="59" />
            </label>
          </div>
        </div>

        <label v-else class="field">
          <span>触发时间</span>
          <input v-model="createForm.time_of_day" type="time" step="1" />
        </label>
      </div>
      <template #actions>
        <button class="button ghost" type="button" @click="createOpen = false">取消</button>
        <button class="button" type="button" @click="submitCreate">创建</button>
      </template>
    </BaseModal>

    <BaseModal
      :open="editOpen"
      title="编辑定时器"
      description="这里只调整触发参数，不修改数据库结构。"
      @close="editOpen = false"
    >
      <div v-if="editForm" class="stack-lg">
        <div class="info-row">
          <span class="label">名称</span>
          <strong>{{ editForm.name }}</strong>
        </div>
        <div v-if="editForm.type === 'once'" class="field">
          <span>延迟秒数</span>
          <input v-model.number="editForm.delay_seconds" type="number" min="1" max="86400" />
        </div>
        <label v-else class="field">
          <span>触发时间</span>
          <input v-model="editForm.time_of_day" type="time" step="1" />
        </label>
      </div>
      <template #actions>
        <button class="button ghost" type="button" @click="editOpen = false">取消</button>
        <button class="button" type="button" @click="submitEdit">保存</button>
      </template>
    </BaseModal>

    <BaseModal
      :open="Boolean(deleteTarget)"
      title="删除定时器"
      description="删除后定时器将从当前列表中移除，已记录的事件不会被修改。"
      width="480px"
      @close="deleteTarget = null"
    >
      <p v-if="deleteTarget" class="modal-copy">
        确认删除“{{ deleteTarget.name }}”？
      </p>
      <template #actions>
        <button class="button ghost" type="button" @click="deleteTarget = null">取消</button>
        <button class="button danger" type="button" @click="confirmDelete">确认删除</button>
      </template>
    </BaseModal>
  </div>
</template>

<style scoped>
.timer-grid {
  display: grid;
  gap: 1rem;
}

.timer-card {
  display: flex;
  justify-content: space-between;
  gap: 1.25rem;
  padding: 1.5rem;
  border-radius: 24px;
  border: 1px solid var(--line);
  background: rgba(255, 250, 244, 0.92);
  box-shadow: var(--shadow-soft);
}

.timer-card__main {
  flex: 1;
}

.timer-card__title-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
}

.timer-card__title-row h2 {
  font-size: 1.2rem;
}

.timer-card__timing {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.8rem;
  margin-top: 1rem;
}

.timer-card__timing > div {
  padding: 0.9rem 1rem;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(123, 92, 55, 0.08);
}

.timer-card__actions {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.4rem 0.7rem;
  border-radius: 999px;
  font-size: 0.86rem;
  background: rgba(201, 126, 62, 0.12);
  color: var(--accent-strong);
}

.status-badge[data-status='completed'] {
  background: rgba(96, 128, 99, 0.14);
  color: #385d3c;
}

.status-badge[data-status='deleted'] {
  background: rgba(176, 67, 46, 0.12);
  color: var(--danger);
}

.pill {
  display: inline-flex;
  padding: 0.3rem 0.65rem;
  border-radius: 999px;
  background: rgba(83, 120, 131, 0.12);
  color: var(--ink-soft);
}

.label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.82rem;
  color: var(--text-muted);
}

.time-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
}

.info-row {
  padding: 1rem;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(123, 92, 55, 0.08);
}

.modal-copy {
  margin: 0;
  color: var(--text-muted);
}

@media (max-width: 760px) {
  .timer-card,
  .timer-card__title-row,
  .timer-card__actions {
    flex-direction: column;
    align-items: stretch;
  }

  .timer-card__timing,
  .time-grid {
    grid-template-columns: 1fr;
  }
}
</style>
