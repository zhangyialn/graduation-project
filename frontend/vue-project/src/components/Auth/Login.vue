<template>
  <div class="login-container">
    <el-card class="login-card" shadow="hover">
      <template #header>
        <div class="login-header">
          <el-avatar :size="60" src="https://img.icons8.com/color/96/000000/car.png" />
          <h2>公务用车管理系统</h2>
        </div>
      </template>
      <el-form :model="form" :rules="rules" ref="loginForm" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="login-btn" @click="handleLogin" :loading="loading">
            登录
          </el-button>
        </el-form-item>
        <el-form-item>
          <el-link type="primary" @click="$router.push('/forgot-password')">
            忘记密码？
          </el-link>
        </el-form-item>
      </el-form>
      <el-alert v-if="error" :title="error" type="error" show-icon class="error-alert" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const form = reactive({
  username: '',
  password: ''
});
const rules = reactive({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
});
const error = ref('');
const loading = ref(false);
const loginForm = ref(null);

const handleLogin = async () => {
  try {
    await loginForm.value.validate();
    loading.value = true;
    const response = await axios.post('/api/auth/login', form);
    localStorage.setItem('token', response.data.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.data.user));
    router.push('/dashboard');
  } catch (err) {
    error.value = err.response?.data?.message || '登录失败，请检查用户名和密码';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f4f7ed 0%, #eff3e6 100%);
  position: relative;
  overflow: hidden;
}

.login-container::before {
  content: '';
  position: absolute;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(107, 142, 35, 0.08) 0%, transparent 70%);
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
  background: radial-gradient(circle, rgba(139, 111, 71, 0.06) 0%, transparent 70%);
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
  background-color: #ffffff;
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

.login-card:hover {
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}

.login-header {
  text-align: center;
  padding: 2rem 0 1.5rem;
  background: linear-gradient(135deg, #f4f7ed 0%, #eff3e6 100%);
  border-bottom: 1px solid #e5ddd2;
}

.login-header h2 {
  margin: 1rem 0 0;
  color: #2d3436;
  font-size: 1.5rem;
  font-weight: 700;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
  background: linear-gradient(135deg, #6b8e23 0%, #556b2f 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
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

.login-btn {
  width: 100% !important;
  margin-bottom: 1rem;
  height: 40px !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
  background: linear-gradient(135deg, #6b8e23 0%, #556b2f 100%) !important;
  border: none !important;
  border-radius: 8px !important;
  color: #ffffff !important;
  transition: all 0.3s ease !important;
}

.login-btn:hover {
  box-shadow: 0 8px 20px rgba(107, 142, 35, 0.3) !important;
  transform: translateY(-2px);
  background: linear-gradient(135deg, #556b2f 0%, #3d5a1f 100%) !important;
}

:deep(.el-link) {
  font-weight: 500;
  transition: all 0.3s ease;
  color: #6b8e23 !important;
}

:deep(.el-link.is-underline:hover) {
  color: #556b2f !important;
}

.error-alert {
  margin-top: 1rem;
  border-radius: 8px;
  border: 1px solid #fde2e4;
  background-color: #fef0f0;
  animation: slideDown 0.3s ease;
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