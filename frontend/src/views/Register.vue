<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
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
  <div class="register-container">
    <h1>注册</h1>
    <div class="form">
      <div class="form-group">
        <label>用户名</label>
        <input v-model="username" type="text" placeholder="请输入用户名" />
      </div>
      <div class="form-group">
        <label>密码</label>
        <input v-model="password" type="password" placeholder="请输入密码" />
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <button @click="register" :disabled="loading">
        {{ loading ? '注册中...' : '注册' }}
      </button>
      <div class="link" @click="goToLogin">已有账号？去登录</div>
    </div>
  </div>
</template>

<style scoped>
.register-container {
  max-width: 400px;
  margin: 100px auto;
  padding: 30px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

h1 {
  text-align: center;
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
}

input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.error {
  color: red;
  margin-bottom: 15px;
}

button {
  width: 100%;
  padding: 12px;
  background: #42b883;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background: #ccc;
}

.link {
  text-align: center;
  margin-top: 15px;
  color: #42b883;
  cursor: pointer;
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .register-container {
    background: #1a1a1a;
    border-color: #333;
  }

  h1 {
    color: #fff;
  }

  label {
    color: #fff;
  }

  input {
    background: #333;
    border-color: #555;
    color: #fff;
  }

  input::placeholder {
    color: #999;
  }

  .link {
    color: #42b883;
  }
}
</style>