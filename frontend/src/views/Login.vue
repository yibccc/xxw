<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import AuthCard from '../components/ui/AuthCard.vue'
import { pushToast, useSession } from '../composables/useSession'

const router = useRouter()
const { loginWithPassword } = useSession()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const login = async () => {
  error.value = ''
  loading.value = true
  try {
    await loginWithPassword(username.value, password.value)
    pushToast({ tone: 'accent', title: '登录成功', message: '欢迎回来。' })
    router.push('/timers')
  } catch (err) {
    error.value = err.response?.data?.error || '登录失败'
  } finally {
    loading.value = false
  }
}

const goToRegister = () => {
  router.push('/register')
}
</script>

<template>
  <div class="auth-layout">
    <AuthCard title="登录" subtitle="继续管理定时器、事件通知和实时提醒。">
      <form class="stack-lg" @submit.prevent="login">
        <label class="field">
          <span>用户名</span>
          <input v-model="username" type="text" placeholder="请输入用户名" />
        </label>
        <label class="field">
          <span>密码</span>
          <input v-model="password" type="password" placeholder="请输入密码" />
        </label>
        <p v-if="error" class="form-error">{{ error }}</p>
        <button class="button" type="submit" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      <template #footer>
        <button class="button ghost auth-link" type="button" @click="goToRegister">没有账号？去注册</button>
      </template>
    </AuthCard>
  </div>
</template>

<style scoped>
.auth-layout {
  min-height: calc(100vh - 3rem);
  display: grid;
  place-items: center;
  padding: 1rem;
}

.auth-link {
  width: 100%;
  justify-content: center;
}
</style>
