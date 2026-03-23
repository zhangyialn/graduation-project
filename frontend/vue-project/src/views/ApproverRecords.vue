<template>
  <div class="page">
    <div class="header-row">
      <div>
        <div class="title">审批记录</div>
        <div class="hint">审批员查看自己的记录或全部记录；按状态筛选</div>
      </div>
      <div class="filters">
        <el-select v-model="status" placeholder="按状态筛选" clearable @change="fetchData">
          <el-option label="全部" value="" />
          <el-option label="通过" value="approved" />
          <el-option label="驳回" value="rejected" />
          <el-option label="待审批" value="pending" />
        </el-select>
        <el-button type="primary" :loading="loading" @click="fetchData">刷新</el-button>
      </div>
    </div>

    <el-alert v-if="error" type="error" show-icon :title="error" class="mb" />

    <el-tabs v-model="activeTab">
      <el-tab-pane label="我的审批" name="mine">
        <el-table :data="myApprovals" size="small">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="application_id" label="申请ID" width="90" />
          <el-table-column prop="status" label="状态" />
          <el-table-column prop="comment" label="意见" />
          <el-table-column prop="created_at" label="时间" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="全部审批" name="all">
        <el-table :data="allApprovals" size="small">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="application_id" label="申请ID" width="90" />
          <el-table-column prop="approver_id" label="审批人" width="90" />
          <el-table-column prop="status" label="状态" />
          <el-table-column prop="comment" label="意见" />
          <el-table-column prop="created_at" label="时间" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const myApprovals = ref([]);
const allApprovals = ref([]);
const status = ref('');
const loading = ref(false);
const error = ref('');
const activeTab = ref('mine');

const token = () => localStorage.getItem('token');
const currentUser = () => {
  const raw = localStorage.getItem('user');
  return raw ? JSON.parse(raw) : null;
};

const fetchData = async () => {
  try {
    loading.value = true;
    error.value = '';
    const headers = { Authorization: `Bearer ${token()}` };
    const user = currentUser();
    const [mineRes, allRes] = await Promise.all([
      user ? axios.get(`/api/approvals/approver/${user.id}`, { headers }) : Promise.resolve({ data: { data: [] } }),
      axios.get(status.value ? `/api/approvals?status=${status.value}` : '/api/approvals', { headers })
    ]);
    myApprovals.value = mineRes.data.data || [];
    allApprovals.value = allRes.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取审批记录失败';
  } finally {
    loading.value = false;
  }
};

onMounted(fetchData);
</script>

<style scoped>
.page {
  padding: 12px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.title {
  font-weight: 700;
  font-size: 1.1rem;
}

.hint {
  color: #6b755a;
}

.filters {
  display: flex;
  gap: 8px;
}

.mb {
  margin-bottom: 12px;
}
</style>
