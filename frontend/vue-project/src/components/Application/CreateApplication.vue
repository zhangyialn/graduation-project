<template>
  <el-card class="application-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon class="header-icon"><DocumentAdd /></el-icon>
        <h2>用车申请</h2>
      </div>
    </template>
    <el-form :model="form" :rules="rules" ref="applicationForm" label-width="120px">
      <el-form-item label="部门ID" prop="department_id">
        <el-input v-model.number="form.department_id" placeholder="请输入部门ID" />
      </el-form-item>
      <el-form-item label="用车事由" prop="purpose">
        <el-input v-model="form.purpose" placeholder="请输入用车事由" />
      </el-form-item>
      <el-form-item label="开始时间" prop="start_time">
        <el-date-picker
          v-model="form.start_time"
          type="datetime"
          placeholder="选择开始时间"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="结束时间" prop="end_time">
        <el-date-picker
          v-model="form.end_time"
          type="datetime"
          placeholder="选择结束时间"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="目的地" prop="destination">
        <el-input v-model="form.destination" placeholder="请输入目的地" />
      </el-form-item>
      <el-form-item label="乘车人数" prop="passenger_count">
        <el-input-number v-model="form.passenger_count" :min="1" :max="10" placeholder="请输入乘车人数" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSubmit" :loading="loading">提交申请</el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
    <el-alert v-if="error" :title="error" type="error" show-icon class="error-alert" />
    <el-alert v-if="success" :title="success" type="success" show-icon class="success-alert" />
  </el-card>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { DocumentAdd } from '@element-plus/icons-vue';

const router = useRouter();
const form = reactive({
  department_id: 1,
  purpose: '',
  start_time: '',
  end_time: '',
  destination: '',
  passenger_count: 1
});
const rules = reactive({
  department_id: [{ required: true, message: '请输入部门ID', trigger: 'blur' }],
  purpose: [{ required: true, message: '请输入用车事由', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  destination: [{ required: true, message: '请输入目的地', trigger: 'blur' }],
  passenger_count: [{ required: true, message: '请输入乘车人数', trigger: 'blur' }]
});
const error = ref('');
const success = ref('');
const loading = ref(false);
const applicationForm = ref(null);

const handleSubmit = async () => {
  try {
    await applicationForm.value.validate();
    loading.value = true;
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    const user = userStr ? JSON.parse(userStr) : null;
    if (!user) {
      error.value = '用户信息不存在';
      return;
    }

    const payload = {
      applicant_id: user.id,
      department_id: form.department_id,
      purpose: form.purpose,
      destination: form.destination,
      passenger_count: form.passenger_count,
      start_time: form.start_time ? new Date(form.start_time).toISOString() : '',
      end_time: form.end_time ? new Date(form.end_time).toISOString() : ''
    };

    await axios.post('/api/applications', payload, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    success.value = '申请提交成功';
    setTimeout(() => {
      router.push('/applications');
    }, 2000);
  } catch (err) {
    error.value = err.response?.data?.message || '提交失败';
  } finally {
    loading.value = false;
  }
};

const resetForm = () => {
  applicationForm.value.resetFields();
};
</script>

<style scoped>
.application-card {
  max-width: 900px;
  margin: 0 auto;
  border-radius: 12px;
  border: 1px solid #e5ddd2;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
  background-color: #ffffff;
}

.application-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: #6b8e23;
}

.card-header {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #f4f7ed 0%, #eff3e6 100%);
  padding: 1.5rem;
  border-bottom: 1px solid #e5ddd2;
}

.header-icon {
  font-size: 1.75rem;
  margin-right: 1rem;
  color: #6b8e23;
}

.card-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
  background: linear-gradient(135deg, #6b8e23 0%, #556b2f 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

:deep(.el-card__body) {
  padding: 2rem;
  background-color: #ffffff;
}

:deep(.el-form-item) {
  margin-bottom: 22px;
}

:deep(.el-form-item__label) {
  color: #2d3436;
  font-weight: 600;
  font-size: 0.95rem;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
}

:deep(.el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  border-radius: 8px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.03);
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
  box-shadow: 0 0 0 3px rgba(107, 142, 35, 0.15);
  outline: none;
}

:deep(.el-input__prefix) {
  color: #8b7355;
}

:deep(.el-input-number .el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  border-radius: 8px;
}

:deep(.el-date-editor) {
  width: 100%;
}

:deep(.el-date-editor .el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  border-radius: 8px;
}

:deep(.el-button.is-primary) {
  height: 40px !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
  background: linear-gradient(135deg, #6b8e23 0%, #556b2f 100%) !important;
  border: none !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
  margin-right: 0.75rem;
  color: #ffffff !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-button.is-primary:hover) {
  box-shadow: 0 8px 20px rgba(107, 142, 35, 0.3) !important;
  transform: translateY(-2px);
  background: linear-gradient(135deg, #556b2f 0%, #3d5a1f 100%) !important;
}

:deep(.el-button:not(.is-primary)) {
  height: 40px !important;
  width: 100% !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
  background-color: #f0f3eb !important;
  border: 1px solid #d4dcc9 !important;
  color: #6b8e23 !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-button:not(.is-primary):hover) {
  background-color: #e5edd8 !important;
  border-color: #c5cdb6 !important;
  color: #556b2f !important;
  transform: translateY(-2px);
}

.error-alert {
  margin-top: 1.5rem;
  border-radius: 8px;
  border: 1px solid #fde2e4;
  background-color: #fef0f0;
  animation: slideDown 0.3s ease;
}

.success-alert {
  margin-top: 1.5rem;
  border-radius: 8px;
  border: 1px solid #c6e2ff;
  background-color: #f0f9ff;
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