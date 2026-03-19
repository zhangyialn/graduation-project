<template>
  <div class="login-container">
    <el-card class="login-card" shadow="hover">
      <template #header>
        <div class="login-header">
          <el-avatar :size="60" src="https://img.icons8.com/color/96/000000/user-plus.png" />
          <h2>用户注册</h2>
        </div>
      </template>
      <el-form :model="form" :rules="rules" ref="registerForm" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色">
            <el-option label="普通用户" value="user" />
            <el-option label="部门领导" value="leader" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门ID" prop="department_id">
          <el-input v-model.number="form.department_id" placeholder="请输入部门ID" prefix-icon="OfficeBuilding" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="login-btn" @click="handleRegister" :loading="loading">
            注册
          </el-button>
          <el-button class="register-btn" @click="$router.push('/login')">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <el-alert v-if="error" :title="error" type="error" show-icon class="error-alert" />
      <el-alert v-if="success" :title="success" type="success" show-icon class="success-alert" />
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
  password: '',
  role: 'user',
  department_id: 1
});
const rules = reactive({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  department_id: [{ required: true, message: '请输入部门ID', trigger: 'blur' }]
});
const error = ref('');
const success = ref('');
const loading = ref(false);
const registerForm = ref(null);

const handleRegister = async () => {
  try {
    await registerForm.value.validate();
    loading.value = true;
    const response = await axios.post('http://localhost:5000/api/auth/register', form);
    success.value = '注册成功，请登录';
    setTimeout(() => {
      router.push('/login');
    }, 2000);
  } catch (err) {
    error.value = err.response?.data?.message || '注册失败';
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
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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

.error-alert, .success-alert {
  margin-top: 1rem;
}
</style>