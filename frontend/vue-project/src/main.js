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
import { notifyWarning } from './utils/notify'

// 配置axios
axios.defaults.baseURL = 'http://localhost:5000'

const authStore = useAuthStore(pinia)
authStore.hydrate()

axios.interceptors.request.use((config) => {
  if (!config.headers.Authorization && authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const requestUrl = String(error?.config?.url || '')
    const isAuthLogin = requestUrl.includes('/api/auth/login')
    if (status === 401 && !isAuthLogin) {
      authStore.clearSession()
      const message = error?.response?.data?.message || '登录状态已失效，请重新登录'
      notifyWarning(message)
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')