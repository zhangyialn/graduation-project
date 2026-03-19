<template>
  <el-card class="application-list-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon class="header-icon"><Document /></el-icon>
        <h2>我的申请</h2>
      </div>
    </template>
    <el-table :data="applications" style="width: 100%" border>
      <el-table-column prop="id" label="申请ID" width="80" />
      <el-table-column prop="purpose" label="用车事由" />
      <el-table-column prop="start_time" label="开始时间" width="180" />
      <el-table-column prop="end_time" label="结束时间" width="180" />
      <el-table-column prop="destination" label="目的地" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="statusType(scope.row.status)">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="scope">
          <el-button type="danger" size="small" @click="cancelApplication(scope.row.id)" v-if="scope.row.status === 'pending'">
            <el-icon><Close /></el-icon>
            取消
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
import { Document, Close } from '@element-plus/icons-vue';

const applications = ref([]);
const error = ref('');

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
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    const user = userStr ? JSON.parse(userStr) : null;
    
    if (!user) {
      error.value = '用户信息不存在';
      return;
    }
    
    const response = await axios.get(`http://localhost:5000/api/applications/my/${user.id}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    applications.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || '获取申请失败';
  }
};

const cancelApplication = async (id) => {
  try {
    const token = localStorage.getItem('token');
    await axios.post(`http://localhost:5000/api/applications/${id}/cancel`, {}, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    fetchApplications();
  } catch (err) {
    error.value = err.response?.data?.message || '取消申请失败';
  }
};

onMounted(() => {
  fetchApplications();
});
</script>

<style scoped>
.application-list-card {
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

.error-alert {
  margin-top: 1rem;
}
</style>

