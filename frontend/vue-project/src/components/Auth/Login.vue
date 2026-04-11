<!-- 登录页：账号登录 + 首个管理员初始化入口展示 -->
<template>
  <div class="login-container">
    <el-card class="login-card" shadow="hover">
      <template #header>
        <div class="login-header">
          <el-avatar :size="60" class="login-logo-avatar">
            <el-icon><SedanIcon /></el-icon>
          </el-avatar>
          <h2>公务用车管理系统</h2>
        </div>
      </template>
      <el-form :model="form" :rules="rules" ref="loginForm" label-position="top" :show-message="false">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <div class="login-options">
          <el-checkbox v-model="form.remember_password">记住密码</el-checkbox>
          <el-checkbox v-model="form.keep_login">保持登录</el-checkbox>
        </div>
        <el-form-item>
          <el-button type="primary" class="login-btn" @click="handleLogin" :loading="loading">
            登录
          </el-button>
        </el-form-item>
        <el-form-item>
          <el-link type="primary" @click="$router.push('/forgot-password')">
            忘记密码？
          </el-link>
          <el-divider v-if="showBootstrapEntry" direction="vertical" />
          <el-link v-if="showBootstrapEntry" type="info" @click="$router.push('/bootstrap-admin')">
            初始化首个管理员
          </el-link>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import SedanIcon from '../Common/SedanIcon.vue';
import { notifyError, notifyWarning } from '../../utils/notify';
import { useAuthStore } from '../../stores/auth';
import { useFuelPriceStore } from '../../stores/fuelPrice';

const router = useRouter();
const authStore = useAuthStore();
const fuelStore = useFuelPriceStore();
const form = reactive({
  username: '',
  password: '',
  remember_password: false,
  keep_login: true
});
const rules = reactive({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
});
const error = ref('');
const loading = ref(false);
const loginForm = ref(null);
const showBootstrapEntry = ref(false);

const REMEMBER_KEY = 'login-remember-password';
const REMEMBER_USERNAME_KEY = 'login-remember-username';
const REMEMBER_PASSWORD_KEY = 'login-remember-password-value';
const KEEP_LOGIN_KEY = 'login-keep-login';

const hasChineseText = (text) => /[\u4e00-\u9fa5]/.test(String(text || ''));

const translateToChinese = async (text) => {
  const raw = String(text || '').trim();
  if (!raw || hasChineseText(raw)) return raw;

  try {
    const response = await axios.post('/api/tools/translate', {
      source_text: raw,
      source: 'en',
      target: 'zh'
    });
    const translated = String(response.data?.data?.target_text || '').trim();
    return translated || raw;
  } catch (_err) {
    return raw;
  }
};

const detectLoginLocation = async () => {
  try {
    const response = await axios.get('/api/tools/login-location');
    const locationText = String(response.data?.data?.location || '').trim();

    if (!locationText) return '未知地点';
    if (hasChineseText(locationText)) return locationText;
    return await translateToChinese(locationText);
  } catch (_err) {
    return '未知地点';
  }
};

const updateLoginMeta = async (username) => {
  if (!username) return;
  const currentKey = `login-current-meta:${username}`;
  const lastKey = `login-last-meta:${username}`;
  const currentRaw = localStorage.getItem(currentKey);
  if (currentRaw) {
    localStorage.setItem(lastKey, currentRaw);
  }
  const location = await detectLoginLocation();
  localStorage.setItem(currentKey, JSON.stringify({
    time: new Date().toISOString(),
    location
  }));
};

// 查询初始化入口状态：仅在系统未创建管理员时显示入口
const fetchBootstrapStatus = async () => {
  try {
    const response = await axios.get('/api/auth/bootstrap-status');
    showBootstrapEntry.value = !!response.data?.data?.enabled;
  } catch (_err) {
    showBootstrapEntry.value = false;
  }
};

// 登录后后台初始化油价，不阻塞主流程
const warmupFuelPriceInBackground = () => {
  Promise.resolve()
    .then(async () => {
      await fuelStore.initializeDailyOilPrice();
      await fuelStore.syncOilPriceToBackend();
    })
    .catch(() => {
      // 油价同步失败不阻断登录
    });
};

// 提交登录并写入会话；首次登录强制跳转改密页
const handleLogin = async () => {
  try {
    await loginForm.value.validate();
    loading.value = true;
    const response = await axios.post('/api/auth/login', {
      username: form.username,
      password: form.password
    });
    const user = response.data.data.user;
    authStore.setSession(response.data.data.access_token, user, form.keep_login ? 'local' : 'session');
    updateLoginMeta(user?.username || form.username).catch(() => {});
    warmupFuelPriceInBackground();

    localStorage.setItem(KEEP_LOGIN_KEY, form.keep_login ? '1' : '0');
    if (form.remember_password) {
      localStorage.setItem(REMEMBER_KEY, '1');
      localStorage.setItem(REMEMBER_USERNAME_KEY, form.username);
      localStorage.setItem(REMEMBER_PASSWORD_KEY, form.password);
    } else {
      localStorage.removeItem(REMEMBER_KEY);
      localStorage.removeItem(REMEMBER_USERNAME_KEY);
      localStorage.removeItem(REMEMBER_PASSWORD_KEY);
    }

    if (user?.must_change_password) {
      notifyWarning('首次登录请先修改密码');
      router.push('/dashboard/change-password');
      return;
    }
    router.push('/dashboard');
  } catch (err) {
    if (err?.response) {
      error.value = err.response?.data?.message || '登录失败，请检查用户名和密码';
      notifyError(error.value);
      return;
    }

    error.value = '';
    notifyWarning('请先填写用户名和密码');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchBootstrapStatus();
  const remembered = localStorage.getItem(REMEMBER_KEY) === '1';
  const keepLogin = localStorage.getItem(KEEP_LOGIN_KEY);
  form.remember_password = remembered;
  form.keep_login = keepLogin === null ? true : keepLogin === '1';
  if (remembered) {
    form.username = localStorage.getItem(REMEMBER_USERNAME_KEY) || '';
    form.password = localStorage.getItem(REMEMBER_PASSWORD_KEY) || '';
  }
});
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: max(16px, env(safe-area-inset-top)) 12px 16px;
  background: #f4f7ed;
  position: relative;
  overflow: hidden;
}

.login-container::before {
  content: '';
  position: absolute;
  width: 400px;
  height: 400px;
  background: rgba(107, 142, 35, 0.08);
  border-radius: 50%;
  top: -100px;
  right: -100px;
  pointer-events: none;
}

.login-container::after {
  content: '';
  position: absolute;
  width: 300px;
  height: 300px;
  background: rgba(139, 111, 71, 0.06);
  border-radius: 50%;
  bottom: -50px;
  left: -50px;
  pointer-events: none;
}

.login-card {
  width: 100%;
  max-width: 450px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5ddd2;
  background-color: transparent;
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

@media (max-width: 768px) {
  .login-container {
    align-items: center;
    padding: max(12px, env(safe-area-inset-top)) 10px 12px;
  }

  .login-card {
    max-width: none;
    border-radius: 14px;
  }

  .login-header {
    padding: 1.5rem 0 1rem;
  }
}

.login-card:hover {
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}

.login-header {
  text-align: center;
  padding: 2rem 0 1.5rem;
  background: transparent;
  border-bottom: 1px solid #e5ddd2;
}

:deep(.login-card.el-card) {
  background-color: transparent !important;
}

:deep(.login-card .el-card__header) {
  background-color: transparent !important;
}

:deep(.login-card .el-card__body) {
  background-color: transparent;
}

.login-header h2 {
  margin: 1rem 0 0;
  color: #1f2a22;
  font-size: 1.5rem;
  font-weight: 700;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
}

.login-logo-avatar {
  background: #eef3df;
  color: #556b2f;
}

.login-logo-avatar :deep(.el-icon) {
  font-size: 28px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  color: #2d3436;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  background-color: #fefdfb;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.03);
  border: 1px solid #e5ddd2;
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #d4c5b9;
  background-color: #ffffff;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05), 0 0 0 3px rgba(107, 142, 35, 0.1);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #6b8e23;
  background-color: #ffffff;
  box-shadow: 0 0 0 4px rgba(107, 142, 35, 0.15);
}

:deep(.el-input__prefix) {
  color: #8b7355;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: -4px 0 12px;
  padding: 2px 2px;
}

:deep(.login-options .el-checkbox) {
  color: #4d5b44;
  font-size: 14px;
}

.login-btn {
  width: 100% !important;
  margin-bottom: 1rem;
  height: 40px !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
  background: #5f7f24 !important;
  border: none !important;
  border-radius: 8px !important;
  color: #ffffff !important;
  transition: all 0.3s ease !important;
}

.login-btn:hover {
  box-shadow: 0 8px 20px rgba(107, 142, 35, 0.3) !important;
  transform: translateY(-2px);
  background: #4f6c1f !important;
}

:deep(.el-link) {
  font-weight: 500;
  transition: all 0.3s ease;
  color: #6b8e23 !important;
}

:deep(.el-link.is-underline:hover) {
  color: #556b2f !important;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
