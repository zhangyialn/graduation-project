<template>
    <el-card class="approval-list-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon class="header-icon"><Check /></el-icon>
        <h2>审批管理</h2>
      </div>
    </template>
    <el-form :inline="true" class="filter-form" @submit.prevent="fetchApplications">
      <el-form-item label="部门ID">
        <el-input v-model.number="departmentId" placeholder="请输入部门ID" style="width: 200px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchApplications" :loading="loading">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
      </el-form-item>
    </el-form>
    <el-table :data="applications" style="width: 100%" border>
      <el-table-column prop="id" label="申请ID" width="80" />
      <el-table-column prop="department_name" label="部门" width="120" />
      <el-table-column prop="purpose" label="用车事由" />
      <el-table-column prop="start_time" label="开始时间" width="180" />
      <el-table-column prop="end_time" label="结束时间" width="180" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="statusType(scope.row.status)">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="scope">
          <el-button type="success" size="small" @click="approveApplication(scope.row.id)">
            <el-icon><Check /></el-icon>
            批准
          </el-button>
          <el-button type="danger" size="small" @click="rejectApplication(scope.row.id)">
            <el-icon><Close /></el-icon>
            拒绝
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-alert v-if="error" :title="error" type="error" show-icon class="error-alert" />
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { Check, Close, Search } from '@element-plus/icons-vue';

const applications = ref([]);
const departmentId = ref(1);
const error = ref('');
const loading = ref(false);

const statusType = (status) => {
  const typeMap = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    completed: 'info'
  };
  return typeMap[status] || 'info';
};

const fetchApplications = async () => {
  try {
    loading.value = true;
    const token = localStorage.getItem('token');
    const response = await axios.get(`http://localhost:5000/api/applications/pending/${departmentId.value}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    applications.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || '获取申请失败';
  } finally {
    loading.value = false;
  }
};

const approveApplication = async (id) => {
  try {
    const token = localStorage.getItem('token');
    await axios.post(`http://localhost:5000/api/approvals`, {
      application_id: id,
      status: 'approved',
      comment: '批准用车申请'
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    fetchApplications();
  } catch (err) {
    error.value = err.response?.data?.message || '审批失败';
  }
};

const rejectApplication = async (id) => {
  try {
    const token = localStorage.getItem('token');
    await axios.post(`http://localhost:5000/api/approvals`, {
      application_id: id,
      status: 'rejected',
      comment: '拒绝用车申请'
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    fetchApplications();
  } catch (err) {
    error.value = err.response?.data?.message || '审批失败';
  }
};

onMounted(() => {
  fetchApplications();
});
</script>

<style scoped>
.approval-list-card {
  max-width: 1200px;
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

.filter-form {
  margin-bottom: 1rem;
}

.error-alert {
  margin-top: 1rem;
}
</style>