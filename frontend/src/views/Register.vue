<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import AuthCard from '../components/ui/AuthCard.vue'
import { pushToast } from '../composables/useSession'
import { authService } from '../services/api'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const register = async () => {
  error.value = ''
  loading.value = true
  try {
    await authService.register(username.value, password.value)
    pushToast({ tone: 'accent', title: '注册成功', message: '现在可以登录并创建定时器。' })
    router.push('/login')
  } catch (err) {
    error.value = err.response?.data?.error || '注册失败'
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="auth-layout">
    <AuthCard title="注册" subtitle="创建一个账号，开始管理一次性和每日定时器。">
      <form class="stack-lg" @submit.prevent="register">
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
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
      <template #footer>
        <button class="button ghost auth-link" type="button" @click="goToLogin">已有账号？去登录</button>
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
