import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/proxies',
    name: 'Proxies',
    component: () => import('../views/Proxies.vue')
  },
  {
    path: '/spider',
    name: 'Spider',
    component: () => import('../views/Spider.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

