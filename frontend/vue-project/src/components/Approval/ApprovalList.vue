<template>
  <div class="approval-container">
    <h2>审批管理</h2>
    <div class="filter">
      <input type="number" v-model="departmentId" placeholder="部门ID">
      <button @click="fetchApplications" class="btn btn-primary">查询</button>
    </div>
    <table class="table">
      <thead>
        <tr>
          <th>申请ID</th>
          <th>部门</th>
          <th>用车事由</th>
          <th>开始时间</th>
          <th>结束时间</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="app in applications" :key="app.id">
          <td>{{ app.id }}</td>
          <td>{{ app.department_name }}</td>
          <td>{{ app.purpose }}</td>
          <td>{{ app.start_time }}</td>
          <td>{{ app.end_time }}</td>
          <td>{{ app.status }}</td>
          <td>
            <button @click="approveApplication(app.id)" class="btn btn-success">批准</button>
            <button @click="rejectApplication(app.id)" class="btn btn-danger">拒绝</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div class="error-message" v-if="error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const applications = ref([]);
const departmentId = ref(1);
const error = ref('');

const fetchApplications = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get(`http://localhost:5000/api/applications/pending/${departmentId.value}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    applications.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || '获取申请失败';
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
.approval-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.filter {
  margin-bottom: 1rem;
  display: flex;
  gap: 1rem;
}

.filter input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  flex: 1;
  max-width: 200px;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.table th, .table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  margin-right: 0.5rem;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.error-message {
  margin-top: 1rem;
  color: #dc3545;
  font-size: 0.875rem;
}
</style>