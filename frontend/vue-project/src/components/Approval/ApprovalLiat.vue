<!-- 审批列表页：展示待审批申请与审批统计 -->
<template>
  <el-card class="approval-card" shadow="hover">
    <template #header>
      <div class="card-header"><el-icon><Check /></el-icon><span>审批管理</span></div>
    </template>

    <div class="toolbar">
      <el-input v-model.number="departmentId" placeholder="部门ID" class="dept-input" />
      <el-button type="primary" :loading="loading" @click="handleQuery">查询</el-button>
    </div>

    <div v-if="isMobile" class="mobile-list">
      <el-card v-for="item in applications" :key="item.id" shadow="never" class="mobile-item">
        <div class="mobile-top">
          <p class="mobile-title">申请 #{{ item.id }}</p>
          <el-tag :type="statusType(item.status)">{{ item.status }}</el-tag>
        </div>
        <p class="mobile-line">申请人：{{ item.applicant_name || '-' }}</p>
        <p class="mobile-line">事由：{{ item.purpose || '-' }}</p>
        <p class="mobile-line">起点：{{ item.start_point || '-' }}</p>
        <p class="mobile-line">终点：{{ item.destination || '-' }}</p>
        <p class="mobile-line">出发时间：{{ formatDate(item.start_time) }}</p>
        <div class="mobile-actions">
          <el-button type="primary" size="small" @click="goDetail(item.id)">进入审批详情</el-button>
        </div>
      </el-card>
    </div>

    <el-table v-else :data="applications" border>
      <el-table-column prop="id" label="申请ID" width="90" />
      <el-table-column prop="applicant_name" label="申请人" width="120" />
      <el-table-column prop="purpose" label="用车事由" />
      <el-table-column prop="start_point" label="起点" width="140" />
      <el-table-column prop="destination" label="终点" width="140" />
      <el-table-column prop="start_time" label="出发时间" width="180">
        <template #default="scope">{{ formatDate(scope.row.start_time) }}</template>
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
      <el-card v-for="item in approvalStats" :key="item.approval_id" shadow="never" class="mobile-item">
        <div class="mobile-top">
          <p class="mobile-title">申请 #{{ item.application_id }}</p>
          <el-tag :type="statusType(item.approval_status)">{{ item.approval_status }}</el-tag>
        </div>
        <p class="mobile-line">申请人：{{ item.applicant_name || '-' }}</p>
        <p class="mobile-line">用车事由：{{ item.purpose || '-' }}</p>
        <p class="mobile-line">起点：{{ item.start_point || '-' }}</p>
        <p class="mobile-line">终点：{{ item.destination || '-' }}</p>
        <p class="mobile-line">用车时间：{{ formatDate(item.start_time) }}</p>
        <p class="mobile-line">审批时间：{{ formatDate(item.approval_time) }}</p>
      </el-card>
    </div>
    <el-table v-else :data="approvalStats" border>
      <el-table-column prop="application_id" label="申请ID" width="90" />
      <el-table-column prop="applicant_name" label="申请人" width="120" />
      <el-table-column prop="purpose" label="用车事由" min-width="200" />
      <el-table-column prop="start_point" label="起点" width="140" />
      <el-table-column prop="destination" label="终点" width="140" />
      <el-table-column prop="start_time" label="用车时间" width="180">
        <template #default="scope">{{ formatDate(scope.row.start_time) }}</template>
      </el-table-column>
      <el-table-column prop="approval_time" label="审批时间" width="180">
        <template #default="scope">{{ formatDate(scope.row.approval_time) }}</template>
      </el-table-column>
      <el-table-column prop="approver_name" label="审批人" width="120" />
      <el-table-column prop="approval_status" label="结果" width="100">
        <template #default="scope"><el-tag :type="statusType(scope.row.approval_status)">{{ scope.row.approval_status }}</el-tag></template>
      </el-table-column>
    </el-table>

  </el-card>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { Check } from '@element-plus/icons-vue';
import { notifyError } from '../../utils/notify';
import { formatBeijingDateTime } from '../../utils/datetime';

const router = useRouter();
const applications = ref([]);
const approvalStats = ref([]);
const departmentId = ref(1);
const error = ref('');
const loading = ref(false);
const screenWidth = ref(window.innerWidth);
const isMobile = computed(() => screenWidth.value < 900);

// 将业务状态映射为标签样式
const statusType = (status) => ({ pending: 'warning', approved: 'success', rejected: 'danger', completed: 'info' }[status] || 'info');
// 时间格式化显示
const formatDate = (value) => formatBeijingDateTime(value);

// 按部门拉取待审批申请
const fetchApplications = async () => {
  try {
    loading.value = true;
    error.value = '';
    const response = await axios.get(`/api/applications/pending/${departmentId.value}`);
    applications.value = response.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取待审批申请失败';
  } finally {
    loading.value = false;
  }
};

// 拉取审批统计数据
const fetchApprovalStatistics = async () => {
  try {
    const response = await axios.get('/api/approvals/statistics', {
      params: { department_id: departmentId.value }
    });
    approvalStats.value = response.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取审批统计失败';
  }
};

const handleQuery = async () => {
  await fetchApplications();
  await fetchApprovalStatistics();
};

// 跳转审批详情页
const goDetail = (id) => router.push(`/dashboard/approvals/${id}`);

// 响应窗口变化，切换桌面/移动布局
const updateWidth = () => {
  screenWidth.value = window.innerWidth;
};

onMounted(() => {
  handleQuery();
  window.addEventListener('resize', updateWidth);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateWidth);
});

watch(error, (message) => {
  if (!message) return;
  notifyError(message);
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
