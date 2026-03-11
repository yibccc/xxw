import { createRouter, createWebHistory } from 'vue-router'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import Timers from './views/Timers.vue'
import Events from './views/Events.vue'

const routes = [
  { path: '/', redirect: '/timers' },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/timers', component: Timers, meta: { requiresAuth: true } },
  { path: '/events', component: Events, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    next('/timers')
  } else {
    next()
  }
})

export default router