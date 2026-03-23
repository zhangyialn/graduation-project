<template>
  <div class="forgot-password-container">
    <el-card class="forgot-password-card" shadow="hover">
      <template #header>
        <div class="forgot-password-header">
          <el-avatar :size="60" :src="forgotPasswordAvatar" />
          <h2>找回密码</h2>
        </div>
      </template>
      
      <el-steps :active="currentStep" align-center class="steps">
        <el-step title="验证身份" />
        <el-step title="设置新密码" />
        <el-step title="完成" />
      </el-steps>
      
      <el-form :model="form" :rules="rules" ref="forgotForm" label-position="top" class="forgot-form">
        <!-- 步骤1：验证身份（用户名 + 手机号） -->
        <div v-if="currentStep === 0">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="form.phone" placeholder="请输入绑定手机号" prefix-icon="Phone" />
          </el-form-item>
          <el-form-item class="action-row">
            <el-button type="primary" class="submit-btn" @click="handleVerify" :loading="loading">
              验证
            </el-button>
            <el-button class="back-btn" @click="$router.push('/login')">
              返回登录
            </el-button>
          </el-form-item>
        </div>
        
        <!-- 步骤2：设置新密码 -->
        <div v-if="currentStep === 1">
          <el-form-item label="新密码" prop="newPassword">
            <el-input v-model="form.newPassword" type="password" placeholder="请输入新密码" prefix-icon="Lock" show-password />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入新密码" prefix-icon="Lock" show-password />
          </el-form-item>
          <el-form-item class="action-row">
            <el-button type="primary" class="submit-btn" @click="handleResetPassword" :loading="loading">
              重置密码
            </el-button>
            <el-button class="back-btn" @click="currentStep = 0">
              上一步
            </el-button>
          </el-form-item>
        </div>
        
        <!-- 步骤3：完成 -->
        <div v-if="currentStep === 2" class="success-step">
          <el-result
            icon="success"
            title="密码重置成功"
            sub-title="请使用新密码登录"
          >
            <template #extra>
              <el-button type="primary" @click="$router.push('/login')">
                返回登录
              </el-button>
            </template>
          </el-result>
        </div>
      </el-form>
      
      <el-alert v-if="error" :title="error" type="error" show-icon class="error-alert" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import axios from 'axios';
import forgotPasswordAvatar from '../../assets/forgot-password.png';

const currentStep = ref(0);
const error = ref('');
const loading = ref(false);
const forgotForm = ref(null);

const form = reactive({
  username: '',
  phone: '',
  newPassword: '',
  confirmPassword: ''
});

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.newPassword) {
    callback(new Error('两次输入的密码不一致'));
  } else {
    callback();
  }
};

const rules = reactive({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
});

const handleVerify = async () => {
  try {
    await forgotForm.value.validateField(['username', 'phone']);
    loading.value = true;
    await axios.post('/api/auth/verify-phone', {
      username: form.username,
      phone: form.phone
    });
    currentStep.value = 1;
    error.value = '';
  } catch (err) {
    error.value = err.response?.data?.message || '验证失败，请检查输入内容';
  } finally {
    loading.value = false;
  }
};

const handleResetPassword = async () => {
  try {
    await forgotForm.value.validateField(['username', 'phone', 'newPassword', 'confirmPassword']);
    loading.value = true;
    await axios.post('/api/auth/reset-password', {
      username: form.username,
      phone: form.phone,
      new_password: form.newPassword
    });
    currentStep.value = 2;
    error.value = '';
  } catch (err) {
    error.value = err.response?.data?.message || '密码重置失败';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.forgot-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f4f7ed;
  position: relative;
  overflow: hidden;
}

.forgot-password-container::before {
  content: '';
  position: absolute;
  width: 400px;
  height: 400px;
  background: rgba(107, 142, 35, 0.1);
  border-radius: 50%;
  top: -100px;
  right: -100px;
  pointer-events: none;
}

.forgot-password-card {
  width: 100%;
  max-width: 500px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.8);
  background-color: transparent;
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

.forgot-password-card:hover {
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.15);
  transform: translateY(-4px);
}

.forgot-password-header {
  text-align: center;
  padding: 2rem 0 1.5rem;
  background: transparent;
  border-bottom: 1px solid #e5ddd2;
}

.forgot-password-header h2 {
  margin: 1rem 0 0;
  color: #1f2a22;
  font-size: 1.5rem;
  font-weight: 700;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
}

:deep(.el-steps) {
  margin: 2rem 0;
}

:deep(.el-step__title) {
  color: #2d3436;
  font-weight: 500;
}

:deep(.el-step.is-process .el-step__title) {
  color: #6b8e23;
  font-weight: 600;
}

:deep(.el-step.is-finish .el-step__title) {
  color: #2d3436;
}

:deep(.el-step__head) {
  background-color: transparent;
}

:deep(.el-step.is-process .el-step__head.is-process) {
  color: #6b8e23;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  color: #2d3436;
  font-weight: 600;
}

.forgot-form {
  margin-top: 1.5rem;
}

:deep(.forgot-password-card.el-card) {
  background-color: transparent !important;
}

:deep(.forgot-password-card .el-card__header) {
  background-color: transparent !important;
}

:deep(.forgot-password-card .el-card__body) {
  background-color: transparent;
}

:deep(.el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  border-radius: 8px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #d4c5b9;
  background-color: #ffffff;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.06), 0 0 0 3px rgba(107, 142, 35, 0.1);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #6b8e23;
  background-color: #ffffff;
  box-shadow: 0 0 0 4px rgba(107, 142, 35, 0.15);
}

:deep(.el-input__prefix) {
  color: #6b8e23;
}

.submit-btn {
  width: 100%;
  margin-bottom: 0;
  height: 40px;
  font-size: 1rem;
  font-weight: 600;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
  background: #5f7f24 !important;
  border: none !important;
  border-radius: 8px;
  color: #ffffff !important;
  transition: all 0.3s ease;
}

.submit-btn:hover {
  box-shadow: 0 8px 20px rgba(107, 142, 35, 0.3) !important;
  transform: translateY(-2px);
  background: #4f6c1f !important;
}

.back-btn {
  width: 100% !important;
  height: 40px !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
  background-color: #f0f3eb !important;
  border: 1px solid #d4dcc9 !important;
  color: #6b8e23 !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}

.back-btn:hover {
  background-color: #e5ede0 !important;
  border-color: #c0cbb8 !important;
  color: #556b2f !important;
  transform: translateY(-2px);
}

.action-row :deep(.el-form-item__content) {
  display: flex;
  gap: 12px;
}

.action-row .submit-btn,
.action-row .back-btn {
  flex: 1 1 0;
}

:deep(.el-result) {
  padding: 0;
}

:deep(.el-result__title) {
  color: #2d3436;
  font-weight: 600;
}

:deep(.el-result__subtitle) {
  color: #6b8e23;
}

.success-step {
  text-align: center;
  padding: 2rem 0;
}

.error-alert {
  margin-top: 1.5rem;
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