<!-- ApplicationList：用户查看与取消本人用车申请 -->
<template>
  <el-card class="application-list-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon class="header-icon"><Document /></el-icon>
        <h2>我的申请</h2>
      </div>
    </template>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      :closable="false"
      class="inline-error"
    />

    <div v-if="pageLoading" class="loading-block">
      <el-skeleton :rows="6" animated />
    </div>

    <template v-else>
    <div v-if="isMobile" class="mobile-list">
      <el-card v-for="item in applications" :key="item.id" shadow="never" class="mobile-item">
        <div class="mobile-top">
          <p class="mobile-title">申请 #{{ item.id }}</p>
          <el-tag :type="statusType(item.status)">{{ item.status }}</el-tag>
        </div>
        <p class="mobile-line">事由：{{ item.purpose || '-' }}</p>
        <p class="mobile-line">起点：{{ item.start_point || '-' }}</p>
        <p class="mobile-line">司机ID：{{ item.driver_id || '-' }}</p>
        <p class="mobile-line">目的地：{{ item.destination || '-' }}</p>
        <p class="mobile-line">出发时间：{{ formatDate(item.start_time) }}</p>
        <div class="mobile-actions" v-if="item.status === 'pending'">
          <el-button type="danger" size="small" @click="cancelApplication(item.id)">取消申请</el-button>
        </div>
      </el-card>
      <el-empty v-if="applications.length === 0" description="暂无申请记录" />
    </div>

    <el-table v-else :data="applications" style="width: 100%" border empty-text="暂无申请记录">
      <el-table-column prop="id" label="申请ID" width="80" />
      <el-table-column prop="purpose" label="用车事由" />
      <el-table-column prop="start_time" label="出发时间" width="180">
        <template #default="scope">{{ formatDate(scope.row.start_time) }}</template>
      </el-table-column>
      <el-table-column prop="start_point" label="起点" width="140" />
      <el-table-column prop="driver_id" label="司机ID" width="90" />
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
    <el-pagination
      v-if="applicationsTotal > applicationsPageSize"
      class="pager"
      background
      layout="prev, pager, next, total"
      :current-page="applicationsPage"
      :page-size="applicationsPageSize"
      :total="applicationsTotal"
      @current-change="onApplicationsPageChange"
    />

    <el-divider>我的行程</el-divider>

    <div v-if="isMobile" class="mobile-list">
      <el-card v-for="item in myTrips" :key="item.application_id" shadow="never" class="mobile-item">
        <div class="mobile-top">
          <p class="mobile-title">行程 #{{ item.trip_id || '-' }}</p>
          <el-tag :type="statusType(item.trip_status || item.dispatch_status || item.application_status)">{{ item.trip_status || item.dispatch_status || item.application_status }}</el-tag>
        </div>
        <p class="mobile-line">事由：{{ item.purpose || '-' }}</p>
        <p class="mobile-line">司机：{{ item.driver_name || '-' }}</p>
        <p class="mobile-line">起点：{{ item.start_point || '-' }}</p>
        <p class="mobile-line">目的地：{{ item.destination || '-' }}</p>
        <p class="mobile-line">费用：{{ item.total_cost ?? '-' }}</p>
        <p class="mobile-line">评分：{{ item.user_rating == null ? '未评分' : `${Number(item.user_rating).toFixed(2)}/5` }}</p>
        <div class="mobile-actions">
          <el-button
            v-if="item.can_end_by_user"
            type="success"
            size="small"
            :loading="tripSubmitting"
            @click="endTrip(item.trip_id)"
          >结束行程</el-button>
          <el-button
            v-if="item.can_rate"
            type="warning"
            size="small"
            @click="openRateDialog(item)"
          >评分</el-button>
        </div>
      </el-card>
      <el-empty v-if="myTrips.length === 0" description="暂无行程记录" />
    </div>

    <el-table v-else :data="myTrips" style="width: 100%" border empty-text="暂无行程记录">
      <el-table-column prop="application_id" label="申请ID" width="90" />
      <el-table-column prop="trip_id" label="行程ID" width="90" />
      <el-table-column prop="purpose" label="事由" min-width="140" />
      <el-table-column prop="driver_name" label="司机" width="120" />
      <el-table-column prop="start_point" label="起点" min-width="120" />
      <el-table-column prop="destination" label="目的地" min-width="120" />
      <el-table-column prop="trip_status" label="行程状态" width="120">
        <template #default="scope">
          <el-tag :type="statusType(scope.row.trip_status || scope.row.dispatch_status || scope.row.application_status)">
            {{ scope.row.trip_status || scope.row.dispatch_status || scope.row.application_status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="actual_start_time" label="开始时间" width="180">
        <template #default="scope">{{ formatDate(scope.row.actual_start_time) }}</template>
      </el-table-column>
      <el-table-column prop="actual_end_time" label="结束时间" width="180">
        <template #default="scope">{{ formatDate(scope.row.actual_end_time) }}</template>
      </el-table-column>
      <el-table-column prop="total_cost" label="费用" width="100">
        <template #default="scope">
          {{ scope.row.total_cost == null ? '-' : Number(scope.row.total_cost).toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="user_rating" label="我的评分" width="120">
        <template #default="scope">
          <span v-if="scope.row.user_rating == null">未评分</span>
          <span v-else>{{ Number(scope.row.user_rating).toFixed(2) }}/5</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="scope">
          <el-button
            v-if="scope.row.can_end_by_user"
            type="success"
            size="small"
            :loading="tripSubmitting"
            @click="endTrip(scope.row.trip_id)"
          >结束行程</el-button>
          <el-button
            v-if="scope.row.can_rate"
            type="warning"
            size="small"
            @click="openRateDialog(scope.row)"
          >评分</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      v-if="tripsTotal > tripsPageSize"
      class="pager"
      background
      layout="prev, pager, next, total"
      :current-page="tripsPage"
      :page-size="tripsPageSize"
      :total="tripsTotal"
      @current-change="onTripsPageChange"
    />

    <el-dialog v-model="rateDialogVisible" title="行程评分" width="420px">
      <el-form label-width="90px">
        <el-form-item label="评分">
          <FractionStarInput v-model="ratingValue" :size="30" :step="0.25" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="tripSubmitting" @click="submitRateTrip">提交评分</el-button>
      </template>
    </el-dialog>
    </template>
  </el-card>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount, watch } from 'vue';
import axios from 'axios';
import { Document, Close } from '@element-plus/icons-vue';
import { useAuthStore } from '../../stores/auth';
import FractionStarInput from '../Common/FractionStarInput.vue';
import { notifyError, notifySuccess, notifyWarning } from '../../utils/notify';
import { formatBeijingDateTime } from '../../utils/datetime';

const authStore = useAuthStore();
const applications = ref([]);
const myTrips = ref([]);
// 两个分页器独立维护，避免“申请列表翻页影响行程列表”的交互串扰。
const applicationsPage = ref(1);
const applicationsPageSize = ref(10);
const applicationsTotal = ref(0);
const tripsPage = ref(1);
const tripsPageSize = ref(10);
const tripsTotal = ref(0);
const error = ref('');
// 仅用于首屏并行加载骨架态，后续翻页不阻塞整页。
const pageLoading = ref(false);
const tripSubmitting = ref(false);
const rateDialogVisible = ref(false);
const currentTripId = ref(null);
const ratingValue = ref(5);
const screenWidth = ref(window.innerWidth);
const isMobile = computed(() => screenWidth.value < 900);

// 将申请状态映射为标签类型
const statusType = (status) => {
  const typeMap = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    completed: 'info',
    dispatched: 'primary',
    started: 'info',
    in_progress: 'info',
    scheduled: 'warning',
    cancelled: 'danger'
  };
  return typeMap[status] || 'info';
};

// 统一格式化日期显示
const formatDate = (value) => {
  return formatBeijingDateTime(value);
};

// 拉取当前登录用户的申请列表
const fetchApplications = async () => {
  try {
    error.value = '';
    const user = authStore.user;
    
    if (!user) {
      error.value = '用户信息不存在';
      return;
    }
    
    const response = await axios.get(`/api/applications/my/${user.id}`, {
      params: {
        page: applicationsPage.value,
        limit: applicationsPageSize.value
      }
    });
    applications.value = response.data.data || [];
    // 兼容后端未返回 pagination 的场景（老接口或异常回退）。
    applicationsTotal.value = response.data?.pagination?.total || applications.value.length;
  } catch (err) {
    error.value = err.response?.data?.message || '获取申请失败';
  }
};

// 拉取当前用户行程，用于“结束行程/评分”
const fetchMyTrips = async () => {
  try {
    error.value = '';
    const response = await axios.get('/api/trips/my', {
      params: {
        page: tripsPage.value,
        limit: tripsPageSize.value
      }
    });
    myTrips.value = response.data?.data || [];
    // 兼容后端未返回 pagination 的场景（老接口或异常回退）。
    tripsTotal.value = response.data?.pagination?.total || myTrips.value.length;
  } catch (err) {
    error.value = err.response?.data?.message || '获取我的行程失败';
  }
};

// 取消待审批申请后刷新列表
const cancelApplication = async (id) => {
  try {
    error.value = '';
    await axios.post(`/api/applications/${id}/cancel`, {});
    await fetchApplications();
    notifySuccess('申请已取消');
  } catch (err) {
    error.value = err.response?.data?.message || '取消申请失败';
  }
};

// 申请列表分页回调。
const onApplicationsPageChange = async (nextPage) => {
  // 申请列表翻页只刷新申请区块数据。
  applicationsPage.value = nextPage;
  await fetchApplications();
};

// 行程列表分页回调。
const onTripsPageChange = async (nextPage) => {
  // 行程列表翻页只刷新行程区块数据。
  tripsPage.value = nextPage;
  await fetchMyTrips();
};

// 用户结束行程（仅乘客本人）
const endTrip = async (tripId) => {
  if (!tripId) return;
  try {
    tripSubmitting.value = true;
    await axios.post(`/api/trips/${tripId}/end`, {});
    notifySuccess('行程已结束');
    await Promise.all([fetchApplications(), fetchMyTrips()]);
  } catch (err) {
    error.value = err.response?.data?.message || '结束行程失败';
  } finally {
    tripSubmitting.value = false;
  }
};

// 打开评分弹窗
const openRateDialog = (row) => {
  if (!row?.trip_id) {
    notifyWarning('行程记录不存在，无法评分');
    return;
  }
  currentTripId.value = row.trip_id;
  ratingValue.value = 5;
  rateDialogVisible.value = true;
};

// 提交评分（0-5，支持小数）
const submitRateTrip = async () => {
  if (!currentTripId.value) return;
  try {
    tripSubmitting.value = true;
    await axios.post(`/api/trips/${currentTripId.value}/rate`, {
      rating: Number(ratingValue.value)
    });
    notifySuccess('评分提交成功');
    rateDialogVisible.value = false;
    await fetchMyTrips();
  } catch (err) {
    error.value = err.response?.data?.message || '评分失败';
  } finally {
    tripSubmitting.value = false;
  }
};

// 更新屏幕宽度用于移动端布局判断
const updateWidth = () => {
  screenWidth.value = window.innerWidth;
};

onMounted(() => {
  // 首屏并行拉取两类数据，保证页面初始化速度。
  pageLoading.value = true;
  Promise.all([fetchApplications(), fetchMyTrips()]).finally(() => {
    pageLoading.value = false;
  });
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
.application-list-card {
  max-width: 1200px;
  margin: 0 auto;
  border-radius: 12px;
  border: 1px solid #e5ddd2;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
  background-color: #ffffff;
}

.application-list-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: #6b8e23;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f8faf5;
  border: 1px solid #e3ead6;
  border-radius: 10px;
  padding: 0.9rem 1.1rem;
  border-bottom: 1px solid #e5ddd2;
}

.inline-error {
  margin-bottom: 14px;
}

.loading-block {
  padding: 10px 4px 4px;
}

.pager {
  margin: 12px 0 8px;
  display: flex;
  justify-content: flex-end;
}

.header-icon {
  font-size: 1.1rem;
  color: #556b2f;
  background: #e9f0dc;
  border: 1px solid #d7e2c2;
  border-radius: 8px;
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.card-header h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
  color: #2d3436;
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

:deep(.el-button) {
  border-radius: 6px !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-button--danger) {
  background-color: #fee2e2 !important;
  border: 1px solid #fecaca !important;
  color: #dc2626 !important;
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

.mobile-list {
  display: grid;
  gap: 10px;
}

.mobile-item {
  border-radius: 10px;
}

.mobile-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mobile-title {
  margin: 0;
  font-weight: 700;
}

.mobile-line {
  margin: 8px 0 0;
  color: #4d5b44;
  font-size: 13px;
}

.mobile-actions {
  margin-top: 10px;
  text-align: right;
}
</style>

