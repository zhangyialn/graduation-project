/**
 * 前端应用入口：初始化 Vue、Pinia、Router、Element Plus，并统一配置 Axios 拦截器。
 */
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { pinia } from './stores/pinia'
import { useAuthStore } from './stores/auth'
import { notifyWarning, resolveApiErrorMessage } from './utils/notify'

// 统一后端 API 地址
axios.defaults.baseURL = 'http://localhost:5000'

const authStore = useAuthStore(pinia)
authStore.hydrate()

// 请求拦截：若本次请求未显式携带 Authorization，则自动注入当前登录 token
axios.interceptors.request.use((config) => {
  if (!config.headers.Authorization && authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

// 响应拦截：标准化后端错误文案；401（非登录接口）时清理会话并跳转登录页
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalizedMessage = resolveApiErrorMessage(error, '请求失败')
    if (error?.response?.data && normalizedMessage) {
      error.response.data.message = normalizedMessage
    }

    const status = error?.response?.status
    const requestUrl = String(error?.config?.url || '')
    const isAuthLogin = requestUrl.includes('/api/auth/login')
    if (status === 401 && !isAuthLogin) {
      authStore.clearSession()
      const message = normalizedMessage || '登录状态已失效，请重新登录'
      notifyWarning(message)
      if (router.currentRoute.value.path !== '/login') {
        router.replace('/login').catch(() => {})
      }
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 全局注册 Element Plus 图标组件
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
