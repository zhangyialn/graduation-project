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
      <el-form-item label="乘车人数" prop="passengers">
        <el-input-number v-model="form.passengers" :min="1" :max="10" placeholder="请输入乘车人数" />
      </el-form-item>
      <el-form-item label="联系电话" prop="contact_phone">
        <el-input v-model="form.contact_phone" placeholder="请输入联系电话" />
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
  passengers: 1,
  contact_phone: ''
});
const rules = reactive({
  department_id: [{ required: true, message: '请输入部门ID', trigger: 'blur' }],
  purpose: [{ required: true, message: '请输入用车事由', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  destination: [{ required: true, message: '请输入目的地', trigger: 'blur' }],
  passengers: [{ required: true, message: '请输入乘车人数', trigger: 'blur' }],
  contact_phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }]
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
    const response = await axios.post('http://localhost:5000/api/applications', form, {
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
  max-width: 800px;
  margin: 0 auto;
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
}

.header-icon {
  font-size: 1.5rem;
  margin-right: 0.75rem;
  color: #409EFF;
}

.card-header h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.error-alert, .success-alert {
  margin-top: 1rem;
}
</style>