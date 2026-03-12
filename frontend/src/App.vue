<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import ToastStack from './components/ui/ToastStack.vue'
import { useSession } from './composables/useSession'

const route = useRoute()
const router = useRouter()
const { state, initializeSession, logout, removeToast } = useSession()

const isAuthRoute = computed(() => ['/login', '/register'].includes(route.path))
const showNav = computed(() => state.user && !isAuthRoute.value)

async function handleLogout() {
  logout()
  await router.push('/login')
}

onMounted(() => {
  initializeSession()
})
</script>

<template>
  <div id="app" class="app-shell">
    <nav v-if="showNav" class="navbar">
      <div class="nav-brand">
        <span class="nav-brand__mark"></span>
        <div>
          <div class="nav-brand__title">定时器服务</div>
          <div class="nav-brand__subtitle">Live scheduling workspace</div>
        </div>
      </div>
      <div class="nav-links">
        <RouterLink to="/timers" active-class="active">定时器</RouterLink>
        <RouterLink to="/events" active-class="active">
          事件
          <span v-if="state.unreadCount" class="nav-pill">{{ state.unreadCount }}</span>
        </RouterLink>
        <div class="nav-meta">
          <span class="status-chip" :data-online="state.sseConnected">
            {{ state.sseConnected ? '实时连接正常' : '实时连接重连中' }}
          </span>
          <span class="user-chip">{{ state.user?.username }}</span>
          <button class="button danger" type="button" @click="handleLogout">退出</button>
        </div>
      </div>
    </nav>

    <main v-if="state.ready" class="app-content">
      <RouterView />
    </main>
    <div v-else class="boot-screen">
      <div class="boot-screen__panel">
        <p class="boot-screen__eyebrow">Preparing workspace</p>
        <h1>正在载入会话</h1>
      </div>
    </div>

    <ToastStack :toasts="state.toasts" @dismiss="removeToast" />
  </div>
</template>

<style>
.app-shell {
  min-height: 100vh;
}

.navbar {
  position: sticky;
  top: 0;
  z-index: 20;
  backdrop-filter: blur(14px);
  background: rgba(255, 249, 241, 0.82);
  border-bottom: 1px solid rgba(123, 92, 55, 0.14);
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.nav-brand__mark {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  box-shadow: 0 0 0 8px rgba(205, 124, 54, 0.12);
}

.nav-brand__title {
  font-weight: 800;
  letter-spacing: -0.03em;
}

.nav-brand__subtitle {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.nav-links {
  display: flex;
  gap: 0.8rem;
  align-items: center;
  flex-wrap: wrap;
}

.nav-links a {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text);
  padding: 0.75rem 1rem;
  border-radius: 999px;
}

.nav-links a:hover {
  background: rgba(205, 124, 54, 0.12);
}

.nav-links a.active {
  background: rgba(205, 124, 54, 0.18);
  color: var(--accent-strong);
}

.nav-pill {
  min-width: 1.45rem;
  padding: 0.12rem 0.42rem;
  border-radius: 999px;
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 0.78rem;
  text-align: center;
}

.nav-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.status-chip,
.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.68rem 0.9rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(123, 92, 55, 0.12);
  color: var(--text-muted);
  font-size: 0.9rem;
}

.status-chip::before {
  content: '';
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 999px;
  background: var(--warn);
}

.status-chip[data-online='true']::before {
  background: var(--success);
}

.app-content {
  padding: 2rem 1.5rem 3rem;
}

.boot-screen {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 1.5rem;
}

.boot-screen__panel {
  width: min(100%, 28rem);
  padding: 2rem;
  border-radius: 28px;
  border: 1px solid var(--line);
  background: rgba(255, 250, 244, 0.92);
  box-shadow: var(--shadow-soft);
}

.boot-screen__eyebrow {
  margin: 0 0 0.5rem;
  font-size: 0.76rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

@media (max-width: 900px) {
  .navbar,
  .nav-links,
  .nav-meta {
    flex-direction: column;
    align-items: stretch;
  }

  .nav-meta {
    width: 100%;
  }

  .app-content {
    padding-inline: 1rem;
  }
}
</style>
