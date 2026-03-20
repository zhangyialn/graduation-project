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
  border-radius: 12px;
  border: 1px solid #e5ddd2;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
  background-color: #ffffff;
}

.approval-list-card:hover {
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

.filter-form {
  padding: 1.5rem;
  background-color: #fefdfb;
  border-bottom: 1px solid #e5ddd2;
  margin-bottom: 0;
}

:deep(.filter-form .el-form-item) {
  margin-bottom: 0;
}

:deep(.filter-form .el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  border-radius: 6px;
}

:deep(.filter-form .el-button.is-primary) {
  background-color: #6b8e23;
  border-color: #6b8e23;
  border-radius: 6px;
}

:deep(.el-table) {
  background-color: transparent;
  border: none;
}

:deep(.el-table__header) {
  background-color: #ffffff;
  border: none;
}

:deep(.el-table__header th) {
  background-color: #f4f7ed;
  border-bottom: 1px solid #e5ddd2;
  font-weight: 600;
  color: #2d3436;
}

:deep(.el-table__body) {
  border: none;
}

:deep(.el-table__body tr) {
  background-color: #ffffff;
  border-bottom: 1px solid #f0ede8;
  transition: all 0.3s ease;
}

:deep(.el-table__body tr:hover) {
  background-color: #fefdfb;
}

:deep(.el-table__body td) {
  border: none;
  padding: 14px 0;
  color: #2d3436;
}

:deep(.el-tag) {
  border-radius: 6px;
  border: none;
  padding: 4px 12px;
  font-weight: 500;
  font-size: 0.85rem;
}

:deep(.el-tag.is-warning) {
  background-color: #fef3c7;
  color: #92400e;
}

:deep(.el-tag.is-success) {
  background-color: #d1fae5;
  color: #065f46;
}

:deep(.el-tag.is-danger) {
  background-color: #fee2e2;
  color: #991b1b;
}

:deep(.el-tag.is-info) {
  background-color: #dbeafe;
  color: #1e40af;
}

:deep(.el-button--success) {
  background-color: #d1fae5 !important;
  border: 1px solid #a7f3d0 !important;
  color: #065f46 !important;
  font-weight: 600 !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-button--success:hover) {
  background-color: #86efac !important;
  border-color: #86efac !important;
  color: #015832 !important;
}

:deep(.el-button--danger) {
  background-color: #fee2e2 !important;
  border: 1px solid #fecaca !important;
  color: #dc2626 !important;
  font-weight: 600 !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-button--danger:hover) {
  background-color: #fca5a5 !important;
  border-color: #fca5a5 !important;
  color: #991b1b !important;
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