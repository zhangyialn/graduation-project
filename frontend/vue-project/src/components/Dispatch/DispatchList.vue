<!-- 调度管理页：调度列表与状态操作 -->
<template>
  <el-card class="dispatch-list-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon class="header-icon"><DataAnalysis /></el-icon>
        <h2>调度管理</h2>
      </div>
    </template>
    
    <!-- 调度列表 -->
    <div v-if="isMobile" class="mobile-list">
      <el-card v-for="item in dispatches" :key="item.id" shadow="never" class="mobile-item">
        <div class="mobile-top">
          <p class="mobile-title">调度 #{{ item.id }}</p>
          <el-tag :type="statusType(item.status)">{{ item.status }}</el-tag>
        </div>
        <p class="mobile-line">申请ID：{{ item.application_id ?? '-' }}</p>
        <p class="mobile-line">车辆ID：{{ item.vehicle_id ?? '-' }}</p>
        <p class="mobile-line">司机ID：{{ item.driver_id ?? '-' }}</p>
        <div class="mobile-actions">
          <el-button type="success" size="small" @click="startDispatch(item.id)" v-if="item.status === 'scheduled'">开始</el-button>
          <el-button type="danger" size="small" @click="cancelDispatch(item.id)" v-if="canCancelDispatch(item)">取消</el-button>
        </div>
      </el-card>
    </div>

    <el-table v-else :data="dispatches" style="width: 100%" border>
      <el-table-column prop="id" label="调度ID" width="80" />
      <el-table-column prop="application_id" label="申请ID" width="100" />
      <el-table-column prop="vehicle_id" label="车辆ID" width="100" />
      <el-table-column prop="driver_id" label="司机ID" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="statusType(scope.row.status)">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="scope">
          <el-button type="success" size="small" @click="startDispatch(scope.row.id)" v-if="scope.row.status === 'scheduled'">
            <el-icon><Check /></el-icon>
            开始
          </el-button>
          <el-button type="danger" size="small" @click="cancelDispatch(scope.row.id)" v-if="canCancelDispatch(scope.row)">
            <el-icon><Close /></el-icon>
            取消
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import axios from 'axios';
import { DataAnalysis, Check, Close } from '@element-plus/icons-vue';
import { notifyError } from '../../utils/notify';

const dispatches = ref([]);
const error = ref('');
const loading = ref(false);
const screenWidth = ref(window.innerWidth);
const isMobile = computed(() => screenWidth.value < 900);

// 将调度状态映射为标签样式
const statusType = (status) => {
  const typeMap = {
    scheduled: 'warning',
    in_progress: 'info',
    completed: 'success',
    cancelled: 'danger'
  };
  return typeMap[status] || 'info';
};

// 仅未开始调度可取消
const canCancelDispatch = (item) => _enumValue(item?.status) === 'scheduled';

const _enumValue = (value) => (value && typeof value === 'object' && 'value' in value ? value.value : value);

// 拉取调度列表
const fetchDispatches = async () => {
  try {
    loading.value = true;
    const response = await axios.get('/api/dispatches');
    dispatches.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || '获取调度失败';
  } finally {
    loading.value = false;
  }
};

// 开始执行调度
const startDispatch = async (id) => {
  try {
    await axios.post(`/api/dispatches/${id}/start`, {});
    await fetchDispatches();
  } catch (err) {
    error.value = err.response?.data?.message || '开始调度失败';
  }
};

// 取消调度
const cancelDispatch = async (id) => {
  try {
    await axios.post(`/api/dispatches/${id}/cancel`, {});
    await fetchDispatches();
  } catch (err) {
    error.value = err.response?.data?.message || '取消调度失败';
  }
};

// 响应窗口变化，切换桌面/移动布局
const updateWidth = () => {
  screenWidth.value = window.innerWidth;
};

onMounted(() => {
  fetchDispatches();
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
.dispatch-list-card {
  max-width: 1200px;
  margin: 0 auto;
  border-radius: 12px;
  border: 1px solid #e5ddd2;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
  background-color: #ffffff;
}

.dispatch-list-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: #6b8e23;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  background: #f8faf5;
  border: 1px solid #e3ead6;
  border-radius: 10px;
  padding: 0.9rem 1.1rem;
  border-bottom: 1px solid #e5ddd2;
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
  flex: 1;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
  color: #2d3436;
}

:deep(.el-button.is-primary) {
  background: #5f7f24 !important;
  border: none !important;
  border-radius: 6px !important;
  color: #ffffff !important;
  font-weight: 600 !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
  height: 40px !important;
}

:deep(.el-button.is-primary:hover) {
  box-shadow: 0 8px 20px rgba(107, 142, 35, 0.3) !important;
  transform: translateY(-2px);
  background: #4f6c1f !important;
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

:deep(.el-tag.is-success) {
  background-color: #d1fae5;
  color: #065f46;
}

:deep(.el-tag.is-warning) {
  background-color: #fef3c7;
  color: #92400e;
}

:deep(.el-tag.is-danger) {
  background-color: #fee2e2;
  color: #991b1b;
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

:deep(.el-dialog) {
  border-radius: 12px;
}

:deep(.el-dialog__header) {
  background: #eef3e5;
  border-bottom: 1px solid #e5ddd2;
}

:deep(.el-dialog__title) {
  color: #2d3436;
  font-weight: 600;
}

:deep(.el-form-item__label) {
  color: #2d3436;
  font-weight: 500;
}

.fuel-meta {
  color: #4a5a35;
  font-size: 0.92rem;
  line-height: 1.4;
}

:deep(.el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  border-radius: 6px;
}

:deep(.el-input__wrapper:hover) {
  border-color: #d4c5b9;
  background-color: #ffffff;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #6b8e23;
  background-color: #ffffff;
}

.error-alert {
  margin-top: 1.5rem;
  border-radius: 8px;
  border: 1px solid #fde2e4;
  background-color: #fef0f0;
  animation: slideDown 0.3s ease;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
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
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 899px) {
  .card-header {
    flex-wrap: wrap;
  }

  .card-header h2 {
    min-width: 100%;
  }

  :deep(.card-header .el-button) {
    width: 100%;
    margin-left: 0 !important;
  }
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
