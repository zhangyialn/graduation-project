<!-- AdminManagement：管理员创建管理员（需二次密码确认） -->
<template>
  <div class="page">
    <el-card class="card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="title">管理员管理</div>
          <div class="hint">仅支持单个新增管理员，默认密码为手机号</div>
        </div>
      </template>

      <el-alert
        type="warning"
        :closable="false"
        show-icon
        title="安全确认"
        description="创建管理员前，需要输入当前登录管理员密码进行二次确认。"
        class="mb"
      />

      <el-form ref="formRef" :model="form" :rules="rules" label-width="130px" class="form">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>

        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="可选，不填自动生成" />
        </el-form-item>

        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="可选" />
        </el-form-item>

        <el-form-item label="部门ID">
          <el-input-number v-model="form.department_id" :min="1" controls-position="right" />
        </el-form-item>

        <el-form-item label="当前管理员密码" prop="operator_password">
          <el-input v-model="form.operator_password" type="password" show-password placeholder="请输入当前管理员密码" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">创建管理员</el-button>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue';
import axios from 'axios';
import { notifyError, notifySuccess } from '../utils/notify';

const loading = ref(false);
const error = ref('');
const success = ref('');
const formRef = ref(null);

const form = reactive({
  name: '',
  phone: '',
  username: '',
  email: '',
  department_id: null,
  operator_password: ''
});

const rules = reactive({
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  operator_password: [{ required: true, message: '请输入当前管理员密码', trigger: 'blur' }]
});

// 提交管理员创建请求
const submit = async () => {
  try {
    await formRef.value.validate();
    loading.value = true;
    error.value = '';
    success.value = '';

    await axios.post('/api/users/admins', {
      name: form.name,
      phone: form.phone,
      username: form.username || undefined,
      email: form.email || undefined,
      department_id: form.department_id || undefined,
      operator_password: form.operator_password
    });

    success.value = '管理员创建成功，默认密码为手机号';
    reset();
  } catch (err) {
    error.value = err.response?.data?.message || '创建管理员失败';
  } finally {
    loading.value = false;
  }
};

// 重置表单内容与校验状态
const reset = () => {
  form.name = '';
  form.phone = '';
  form.username = '';
  form.email = '';
  form.department_id = null;
  form.operator_password = '';
  formRef.value?.clearValidate();
};

watch(error, (message) => {
  if (!message) return;
  notifyError(message);
});

watch(success, (message) => {
  if (!message) return;
  notifySuccess(message);
});
</script>

<style scoped>
.page {
  padding: 12px;
}

.card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #2d3436;
}

.hint {
  color: #667459;
  font-size: 0.95rem;
}

.form {
  max-width: 760px;
}

.mb {
  margin-bottom: 12px;
}
</style>
