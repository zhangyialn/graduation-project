

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// 配置axios
axios.defaults.baseURL = 'http://localhost:5000'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
