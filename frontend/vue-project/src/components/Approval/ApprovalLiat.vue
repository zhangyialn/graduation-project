<template>
  <el-card class="approval-card" shadow="hover">
    <template #header>
      <div class="card-header"><el-icon><Check /></el-icon><span>审批管理</span></div>
    </template>

    <div class="toolbar">
      <el-input v-model.number="departmentId" placeholder="部门ID" class="dept-input" />
      <el-button type="primary" :loading="loading" @click="fetchApplications">查询</el-button>
    </div>

    <div v-if="isMobile" class="mobile-list">
      <el-card v-for="item in applications" :key="item.id" shadow="never" class="mobile-item">
        <div class="mobile-top">
          <p class="mobile-title">申请 #{{ item.id }}</p>
          <el-tag :type="statusType(item.status)">{{ item.status }}</el-tag>
        </div>
        <p class="mobile-line">事由：{{ item.purpose || '-' }}</p>
        <p class="mobile-line">时间：{{ formatDate(item.start_time) }} - {{ formatDate(item.end_time) }}</p>
        <div class="mobile-actions">
          <el-button type="primary" size="small" @click="goDetail(item.id)">进入审批详情</el-button>
        </div>
      </el-card>
    </div>

    <el-table v-else :data="applications" border>
      <el-table-column prop="id" label="申请ID" width="90" />
      <el-table-column prop="purpose" label="用车事由" />
      <el-table-column prop="start_time" label="开始时间" width="180">
        <template #default="scope">{{ formatDate(scope.row.start_time) }}</template>
      </el-table-column>
      <el-table-column prop="end_time" label="结束时间" width="180">
        <template #default="scope">{{ formatDate(scope.row.end_time) }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="110">
        <template #default="scope"><el-tag :type="statusType(scope.row.status)">{{ scope.row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="scope"><el-button type="primary" size="small" @click="goDetail(scope.row.id)">审批详情</el-button></template>
      </el-table-column>
    </el-table>

    <el-divider>审批统计</el-divider>
    <div v-if="isMobile" class="mobile-list">
      <el-card v-for="item in approvalStats" :key="item.approver_name" shadow="never" class="mobile-item">
        <p class="mobile-title">{{ item.approver_name || '-' }}</p>
        <p class="mobile-line">总数：{{ item.total_count ?? 0 }}</p>
        <p class="mobile-line">同意：{{ item.approved_count ?? 0 }}</p>
        <p class="mobile-line">驳回：{{ item.rejected_count ?? 0 }}</p>
      </el-card>
    </div>
    <el-table v-else :data="approvalStats" border>
      <el-table-column prop="approver_name" label="审批人" />
      <el-table-column prop="total_count" label="总数" width="100" />
      <el-table-column prop="approved_count" label="同意" width="100" />
      <el-table-column prop="rejected_count" label="驳回" width="100" />
    </el-table>

    <el-alert v-if="error" :title="error" type="error" show-icon class="mt" />
  </el-card>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { Check } from '@element-plus/icons-vue';

const router = useRouter();
const applications = ref([]);
const approvalStats = ref([]);
const departmentId = ref(1);
const error = ref('');
const loading = ref(false);
const screenWidth = ref(window.innerWidth);
const isMobile = computed(() => screenWidth.value < 900);

const statusType = (status) => ({ pending: 'warning', approved: 'success', rejected: 'danger', completed: 'info' }[status] || 'info');
const formatDate = (v) => v ? new Date(v).toLocaleString() : '-';

const fetchApplications = async () => {
  try {
    loading.value = true;
    error.value = '';
    const token = localStorage.getItem('token');
    const response = await axios.get(`/api/applications/pending/${departmentId.value}`, { headers: { Authorization: `Bearer ${token}` } });
    applications.value = response.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取待审批申请失败';
  } finally {
    loading.value = false;
  }
};

const fetchApprovalStatistics = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get('/api/approvals/statistics', { headers: { Authorization: `Bearer ${token}` } });
    approvalStats.value = response.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取审批统计失败';
  }
};

const goDetail = (id) => router.push(`/dashboard/approvals/${id}`);

const updateWidth = () => {
  screenWidth.value = window.innerWidth;
};

onMounted(() => {
  fetchApplications();
  fetchApprovalStatistics();
  window.addEventListener('resize', updateWidth);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateWidth);
});
</script>

<style scoped>
.approval-card { max-width: 1200px; margin: 0 auto; }
.card-header { display: flex; gap: 8px; align-items: center; font-weight: 700; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
.dept-input { width: 180px; }
.mobile-list { display: grid; gap: 10px; }
.mobile-item { border-radius: 10px; }
.mobile-top { display: flex; justify-content: space-between; align-items: center; }
.mobile-title { margin: 0; font-weight: 700; }
.mobile-line { margin: 8px 0 0; color: #4d5b44; font-size: 13px; }
.mobile-actions { margin-top: 10px; text-align: right; }
.mt { margin-top: 12px; }
@media (max-width: 899px) { .toolbar { flex-direction: column; } .dept-input { width: 100%; } }
</style>
