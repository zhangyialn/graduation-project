<template>
  <div class="forgot-password-container">
    <el-card class="forgot-password-card" shadow="hover">
      <template #header>
        <div class="forgot-password-header">
          <el-avatar :size="60" src="https://img.icons8.com/color/96/000000/forgot-password.png" />
          <h2>找回密码</h2>
        </div>
      </template>
      
      <el-steps :active="currentStep" align-center class="steps">
        <el-step title="验证身份" />
        <el-step title="设置新密码" />
        <el-step title="完成" />
      </el-steps>
      
      <el-form :model="form" :rules="rules" ref="forgotForm" label-position="top" class="forgot-form">
        <!-- 步骤1：验证身份 -->
        <div v-if="currentStep === 0">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="form.phone" placeholder="请输入绑定的手机号" prefix-icon="Phone" />
          </el-form-item>
          <el-form-item>
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
          <el-form-item>
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
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
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
    await forgotForm.value.validate();
    loading.value = true;
    await axios.post('http://localhost:5000/api/auth/verify', {
      username: form.username,
      phone: form.phone
    });
    currentStep.value = 1;
    error.value = '';
  } catch (err) {
    error.value = err.response?.data?.message || '身份验证失败，请检查用户名和手机号';
  } finally {
    loading.value = false;
  }
};

const handleResetPassword = async () => {
  try {
    await forgotForm.value.validate();
    loading.value = true;
    await axios.post('http://localhost:5000/api/auth/reset-password', {
      username: form.username,
      phone: form.phone,
      newPassword: form.newPassword
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
  background-color: #f4f7ed;
}

.forgot-password-card {
  width: 100%;
  max-width: 500px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.forgot-password-header {
  text-align: center;
  padding: 1rem 0;
}

.forgot-password-header h2 {
  margin: 1rem 0 0;
  color: #303133;
  font-size: 1.5rem;
  font-weight: 600;
}

.steps {
  margin: 2rem 0;
}

.forgot-form {
  margin-top: 2rem;
}

.submit-btn {
  width: 100%;
  margin-bottom: 0.5rem;
}

.back-btn {
  width: 100%;
}

.success-step {
  text-align: center;
  padding: 2rem 0;
}

.error-alert {
  margin-top: 1rem;
}
</style>