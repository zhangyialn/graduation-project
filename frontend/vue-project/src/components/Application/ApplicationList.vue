<template>
  <div class="application-list">
    <h2>我的申请</h2>
    <table class="table">
      <thead>
        <tr>
          <th>申请ID</th>
          <th>用车事由</th>
          <th>开始时间</th>
          <th>结束时间</th>
          <th>目的地</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="app in applications" :key="app.id">
          <td>{{ app.id }}</td>
          <td>{{ app.purpose }}</td>
          <td>{{ app.start_time }}</td>
          <td>{{ app.end_time }}</td>
          <td>{{ app.destination }}</td>
          <td>{{ app.status }}</td>
          <td>
            <button @click="cancelApplication(app.id)" class="btn btn-danger" v-if="app.status === 'pending'">取消</button>
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
const error = ref('');

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
.application-list {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
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