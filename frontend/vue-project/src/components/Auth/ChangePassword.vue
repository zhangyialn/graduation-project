<template>
  <el-card class="change-password-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon class="header-icon"><Lock /></el-icon>
        <h2>修改密码</h2>
      </div>
    </template>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
      <el-form-item label="旧密码" prop="old_password">
        <el-input v-model="form.old_password" type="password" show-password placeholder="请输入旧密码" />
      </el-form-item>

      <el-form-item label="新密码" prop="new_password">
        <el-input v-model="form.new_password" type="password" show-password placeholder="请输入新密码（至少6位）" />
      </el-form-item>

      <el-form-item label="确认新密码" prop="confirm_password">
        <el-input v-model="form.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="loading" @click="handleSubmit">确认修改</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive, ref } from 'vue';
import axios from 'axios';
import { Lock } from '@element-plus/icons-vue';
import { notifyError, notifySuccess } from '../../utils/notify';

const loading = ref(false);
const formRef = ref(null);
const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
});

const validateConfirmPassword = (_rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入新密码'));
    return;
  }
  if (value !== form.new_password) {
    callback(new Error('两次输入的新密码不一致'));
    return;
  }
  callback();
};

const rules = reactive({
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码至少6位', trigger: 'blur' }
  ],
  confirm_password: [{ validator: validateConfirmPassword, trigger: 'blur' }]
});

const handleSubmit = async () => {
  try {
    await formRef.value.validate();
    loading.value = true;

    await axios.post('/api/auth/change-password', {
      old_password: form.old_password,
      new_password: form.new_password
    });

    notifySuccess('密码修改成功，请牢记新密码');
    handleReset();
  } catch (err) {
    notifyError(err.response?.data?.message || '密码修改失败');
  } finally {
    loading.value = false;
  }
};

const handleReset = () => {
  form.old_password = '';
  form.new_password = '';
  form.confirm_password = '';
  formRef.value?.clearValidate();
};
</script>

<style scoped>
.change-password-card {
  max-width: 780px;
  margin: 0 auto;
  border-radius: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  color: #556b2f;
}

.card-header h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
}
</style>
