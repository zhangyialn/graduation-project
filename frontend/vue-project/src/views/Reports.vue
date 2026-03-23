<template>
  <div class="page">
    <div class="header-row">
      <div>
        <div class="title">报表与可视化</div>
        <div class="hint">消费 /api/reports/* 接口，展示部门、车辆、司机、用户等统计</div>
      </div>
      <el-button type="primary" :loading="loading" @click="fetchAll">刷新数据</el-button>
    </div>

    <el-alert v-if="error" type="error" show-icon :title="error" class="mb" />

    <div class="grid">
      <el-card shadow="hover">
        <template #header>
          <div class="card-title">部门用车频率</div>
        </template>
        <div v-for="item in departmentUsage" :key="item.department_id" class="bar-row">
          <div class="label">{{ item.department_name }}</div>
          <div class="bar">
            <div class="fill" :style="{ width: barWidth(item.total_count, maxDepartmentCount) }"></div>
          </div>
          <div class="value">{{ item.total_count }} 次</div>
        </div>
      </el-card>

      <el-card shadow="hover">
        <template #header>
          <div class="card-title">部门费用统计</div>
        </template>
        <el-table :data="departmentExpenses" size="small">
          <el-table-column prop="department_name" label="部门" />
          <el-table-column prop="total_expense" label="总费用" />
          <el-table-column prop="fuel_expense" label="燃油" />
          <el-table-column prop="maintenance_expense" label="维修" />
          <el-table-column prop="other_expense" label="其他" />
        </el-table>
      </el-card>

      <el-card shadow="hover">
        <template #header>
          <div class="card-title">车辆使用与费用</div>
        </template>
        <el-table :data="vehicleUsage" size="small">
          <el-table-column prop="plate_number" label="车牌" />
          <el-table-column prop="model" label="车型" />
          <el-table-column prop="usage_count" label="使用次数" />
          <el-table-column prop="total_mileage" label="里程(km)" />
          <el-table-column prop="total_expense" label="费用" />
        </el-table>
      </el-card>

      <el-card shadow="hover">
        <template #header>
          <div class="card-title">月度用车趋势</div>
        </template>
        <div v-for="item in monthlyStats" :key="item.month" class="bar-row">
          <div class="label">{{ item.month }}月</div>
          <div class="bar">
            <div class="fill" :style="{ width: barWidth(item.application_count, maxMonthlyCount) }"></div>
          </div>
          <div class="value">{{ item.application_count }} 次 / ¥{{ item.total_expense }}</div>
        </div>
      </el-card>

      <el-card shadow="hover">
        <template #header>
          <div class="card-title">司机工作量</div>
        </template>
        <el-table :data="driverWorkload" size="small">
          <el-table-column prop="driver_name" label="司机" />
          <el-table-column prop="trip_count" label="行程数" />
          <el-table-column prop="total_mileage" label="里程(km)" />
        </el-table>
      </el-card>

      <el-card shadow="hover">
        <template #header>
          <div class="card-title">用户用车统计</div>
        </template>
        <el-table :data="userStats" size="small">
          <el-table-column prop="user_name" label="用户" />
          <el-table-column prop="application_count" label="申请数" />
          <el-table-column prop="usage_count" label="用车次数" />
          <el-table-column prop="total_expense" label="总费用" />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const loading = ref(false);
const error = ref('');
const departmentUsage = ref([]);
const departmentExpenses = ref([]);
const vehicleUsage = ref([]);
const monthlyStats = ref([]);
const driverWorkload = ref([]);
const userStats = ref([]);

const token = () => localStorage.getItem('token');

const fetchAll = async () => {
  try {
    loading.value = true;
    error.value = '';
    const headers = { Authorization: `Bearer ${token()}` };
    const [deptUse, deptExp, vehicle, monthly, driver, user] = await Promise.all([
      axios.get('/api/reports/department-usage', { headers }),
      axios.get('/api/reports/department-expenses', { headers }),
      axios.get('/api/reports/vehicle-usage', { headers }),
      axios.get('/api/reports/monthly-stats', { headers }),
      axios.get('/api/reports/driver-workload', { headers }),
      axios.get('/api/reports/user-application-stats', { headers })
    ]);
    departmentUsage.value = deptUse.data.data || [];
    departmentExpenses.value = deptExp.data.data || [];
    vehicleUsage.value = vehicle.data.data || [];
    monthlyStats.value = monthly.data.data || [];
    driverWorkload.value = driver.data.data || [];
    userStats.value = user.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取报表数据失败';
  } finally {
    loading.value = false;
  }
};

const maxDepartmentCount = computed(() => Math.max(...departmentUsage.value.map(i => Number(i.total_count) || 0), 1));
const maxMonthlyCount = computed(() => Math.max(...monthlyStats.value.map(i => Number(i.application_count) || 0), 1));

const barWidth = (value, max) => {
  const v = Number(value) || 0;
  const m = Number(max) || 1;
  const pct = Math.min(100, (v / m) * 100);
  return `${pct}%`;
};

onMounted(fetchAll);
</script>

<style scoped>
.page {
  padding: 12px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.mb {
  margin-bottom: 12px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 12px;
}

.card-title {
  font-weight: 700;
}

.bar-row {
  display: grid;
  grid-template-columns: 1fr 2fr auto;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.label {
  color: #2d3436;
}

.bar {
  background: #f0f3eb;
  border-radius: 6px;
  height: 12px;
  overflow: hidden;
}

.fill {
  height: 100%;
  background: linear-gradient(135deg, #6b8e23 0%, #556b2f 100%);
}

.value {
  color: #6b755a;
  font-size: 0.95rem;
}
</style>
