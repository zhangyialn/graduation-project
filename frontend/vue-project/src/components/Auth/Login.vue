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
          <el-button class="register-btn" @click="$router.push('/register')">
            注册
          </el-button>
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
    const response = await axios.post('http://localhost:5000/api/auth/login', form);
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 100%;
  max-width: 450px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  padding: 1rem 0;
}

.login-header h2 {
  margin: 1rem 0 0;
  color: #303133;
  font-size: 1.5rem;
  font-weight: 600;
}

.login-btn {
  width: 100%;
  margin-bottom: 0.5rem;
}

.register-btn {
  width: 100%;
}

.error-alert {
  margin-top: 1rem;
}
</style>