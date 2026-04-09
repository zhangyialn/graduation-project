<template>
  <el-card class="trip-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span>行程管理</span>
        <el-button type="primary" :loading="loading" @click="fetchTrips">刷新</el-button>
      </div>
    </template>

    <div v-if="isMobile" class="mobile-list">
      <el-card v-for="item in trips" :key="item.trip_id" shadow="never" class="mobile-item">
        <p class="mobile-line">乘客姓名：{{ item.passenger_name || '-' }}</p>
        <p class="mobile-line">司机姓名：{{ item.driver_name || '-' }}</p>
        <p class="mobile-line">乘车事由：{{ item.purpose || '-' }}</p>
        <p class="mobile-line">路程：{{ formatNumber(item.distance_km) }} km</p>
        <p class="mobile-line">油耗：{{ formatNumber(item.fuel_used_l) }} L</p>
        <p class="mobile-line">费用：{{ formatMoney(item.total_cost) }} 元</p>
        <p class="mobile-line">接到乘客：{{ item.passenger_picked_up ? '是' : '否' }}</p>
      </el-card>
    </div>
    <el-pagination
      v-if="total > pageSize"
      class="pager"
      background
      layout="prev, pager, next, total"
      :current-page="page"
      :page-size="pageSize"
      :total="total"
      @current-change="onPageChange"
    />

    <el-table v-else :data="trips" border>
      <el-table-column prop="passenger_name" label="乘客姓名" min-width="120" />
      <el-table-column prop="driver_name" label="司机姓名" min-width="120" />
      <el-table-column prop="purpose" label="乘客乘车事由" min-width="220" />
      <el-table-column prop="distance_km" label="路程(km)" width="120">
        <template #default="scope">{{ formatNumber(scope.row.distance_km) }}</template>
      </el-table-column>
      <el-table-column prop="fuel_used_l" label="油耗(L)" width="110">
        <template #default="scope">{{ formatNumber(scope.row.fuel_used_l) }}</template>
      </el-table-column>
      <el-table-column prop="total_cost" label="费用(元)" width="120">
        <template #default="scope">{{ formatMoney(scope.row.total_cost) }}</template>
      </el-table-column>
      <el-table-column prop="passenger_picked_up" label="接到乘客" width="100">
        <template #default="scope">{{ scope.row.passenger_picked_up ? '是' : '否' }}</template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import axios from 'axios';
import { notifyError } from '../../utils/notify';

const loading = ref(false);
const error = ref('');
const trips = ref([]);
// 行程管理页使用后端分页，避免一次性加载所有历史行程。
const page = ref(1);
const pageSize = ref(12);
const total = ref(0);
const screenWidth = ref(window.innerWidth);
const isMobile = computed(() => screenWidth.value < 900);

// 统一数值显示：保留两位小数，不可用数据返回占位符。
const formatNumber = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
  return Number(value).toFixed(2);
};

// 统一金额显示：保留两位小数，不可用数据返回占位符。
const formatMoney = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
  return Number(value).toFixed(2);
};

// 拉取行程管理列表（支持分页）。
const fetchTrips = async () => {
  try {
    loading.value = true;
    error.value = '';
    const response = await axios.get('/api/trips/management', {
      params: {
        page: page.value,
        limit: pageSize.value
      }
    });
    trips.value = response.data?.data || [];
    // 兼容后端未返回 pagination 的场景（老接口或兜底响应）。
    total.value = response.data?.pagination?.total || trips.value.length;
  } catch (err) {
    error.value = err.response?.data?.message || '获取行程列表失败';
  } finally {
    loading.value = false;
  }
};

// 分页器触发后更新当前页并重新请求该页数据。
const onPageChange = async (nextPage) => {
  // 翻页后仅刷新行程列表，不影响当前筛选与布局状态。
  page.value = nextPage;
  await fetchTrips();
};

// 根据窗口宽度切换桌面/移动布局。
const updateWidth = () => {
  screenWidth.value = window.innerWidth;
};

onMounted(() => {
  fetchTrips();
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
.trip-card { border: none; }
.card-header { display: flex; align-items: center; justify-content: space-between; font-weight: 700; }
.mobile-list { display: grid; gap: 10px; }
.mobile-item { border-radius: 10px; }
.mobile-line { margin: 6px 0 0; color: #4d5b44; font-size: 13px; }
.pager { margin: 12px 0 8px; justify-content: flex-end; display: flex; }
</style>
