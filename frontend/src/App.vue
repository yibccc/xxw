<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const showNav = computed(() => {
  return ['/login', '/register'].includes(router.currentRoute.value.path)
})
</script>

<template>
  <div id="app">
    <nav v-if="!showNav" class="navbar">
      <div class="nav-brand">定时器服务</div>
      <div class="nav-links">
        <router-link to="/timers" active-class="active">定时器</router-link>
        <router-link to="/events" active-class="active">事件</router-link>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  max-width: 100%;
  margin: 0;
  padding: 0;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
}

.navbar {
  background: #2c3e50;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.nav-brand {
  color: white;
  font-size: 20px;
  font-weight: bold;
}

.nav-links {
  display: flex;
  gap: 20px;
}

.nav-links a {
  color: #ecf0f1;
  text-decoration: none;
  padding: 10px 15px;
  border-radius: 4px;
  transition: background 0.3s;
}

.nav-links a:hover {
  background: #34495e;
}

.nav-links a.active {
  background: #42b883;
}
</style>
