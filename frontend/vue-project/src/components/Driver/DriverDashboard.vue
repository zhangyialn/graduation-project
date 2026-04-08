<!-- 司机工作台：司机状态、车辆状态、当前任务填报与评分展示 -->
<template>
  <el-card class="driver-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>司机主面板</span>
        <el-button type="primary" @click="fetchDashboard" :loading="loading">刷新</el-button>
      </div>
    </template>

    <el-row :gutter="12" class="meta-row">
      <el-col :xs="24" :sm="8">
        <el-card shadow="never">
          <p class="meta-title">司机状态</p>
          <el-tag :type="statusType(driver?.status)">{{ driver?.status || '-' }}</el-tag>
          <el-select v-model="driverStatus" placeholder="更新司机状态" class="mt" style="width:100%">
            <el-option label="可用" value="available" />
            <el-option label="不可用" value="unavailable" />
          </el-select>
          <el-button class="mt" type="primary" plain @click="updateDriverStatus" :loading="saving">保存司机状态</el-button>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="8">
        <el-card shadow="never">
          <p class="meta-title">车辆状态</p>
          <p>车牌：{{ vehicle?.plate_number || '-' }}</p>
          <el-tag :type="statusType(vehicle?.status)">{{ vehicle?.status || '-' }}</el-tag>
          <el-select v-model="vehicleStatus" placeholder="更新车辆状态" class="mt" style="width:100%">
            <el-option label="可用" value="available" />
            <el-option label="维修中" value="maintenance" />
            <el-option label="不可用" value="unavailable" />
          </el-select>
          <el-button class="mt" type="primary" plain @click="updateVehicleStatus" :loading="saving">保存车辆状态</el-button>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="8">
        <el-card shadow="never">
          <p class="meta-title">更换绑定车辆</p>
          <el-input v-model="plateNumber" placeholder="请输入车牌号" />
          <el-button class="mt" type="primary" plain @click="bindVehicle" :loading="saving">按车牌绑定</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12" class="meta-row">
      <el-col :xs="24" :sm="12">
        <el-card shadow="never">
          <p class="meta-title">司机评分均分</p>
          <p v-if="driverRatingAvg === null" class="empty">暂无乘客评分</p>
          <FractionStarDisplay
            v-else
            :score="driverRatingAvg || 0"
            :size="24"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-divider>接驾任务</el-divider>

    <div v-if="tasks.length === 0" class="empty">暂无待执行任务</div>

    <el-table v-else :data="tasks" border>
      <el-table-column prop="application_id" label="申请ID" width="90" />
      <el-table-column prop="start_time" label="出发时间" width="180">
        <template #default="scope">{{ formatDate(scope.row.start_time) }}</template>
      </el-table-column>
      <el-table-column prop="start_point" label="起点" min-width="140" />
      <el-table-column prop="passenger_phone" label="乘客电话" width="140" />
      <el-table-column prop="destination" label="目的地" min-width="140" />
      <el-table-column prop="dispatch_status" label="调度状态" width="120">
        <template #default="scope">
          <el-tag :type="statusType(scope.row.dispatch_status)">{{ scope.row.dispatch_status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="actual_start_time" label="行程开始" width="180">
        <template #default="scope">{{ formatDate(scope.row.actual_start_time) }}</template>
      </el-table-column>
      <el-table-column prop="user_rating" label="乘客评分" width="120">
        <template #default="scope">
          <span v-if="scope.row.user_rating === null || scope.row.user_rating === undefined">未评分</span>
          <span v-else>{{ Number(scope.row.user_rating).toFixed(2) }}/5</span>
        </template>
      </el-table-column>
      <el-table-column label="行程填报" width="240" fixed="right">
        <template #default="scope">
          <el-button
            v-if="scope.row.trip_id && !scope.row.passenger_picked_up"
            type="primary"
            size="small"
            @click="pickupPassenger(scope.row)"
            :loading="saving"
          >已接到乘客</el-button>
          <el-button
            v-else-if="scope.row.trip_id"
            type="success"
            size="small"
            @click="openReportDialog(scope.row)"
          >填报里程油耗</el-button>
          <span v-else>未创建行程记录</span>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="reportDialogVisible" title="司机里程油耗填报" width="420px">
      <el-form :model="reportForm" label-width="100px">
        <el-form-item label="路程(km)">
          <el-input-number v-model="reportForm.distance_km" :min="0" :step="0.1" style="width:100%" />
        </el-form-item>
        <el-form-item label="油耗(L)">
          <el-input-number v-model="reportForm.fuel_used" :min="0" :step="0.1" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reportDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDriverReport" :loading="saving">提交</el-button>
      </template>
    </el-dialog>

    <el-divider>已完成行程（最近30条）</el-divider>
    <div v-if="completedTrips.length === 0" class="empty">暂无已完成行程</div>
    <el-table v-else :data="completedTrips" border>
      <el-table-column prop="trip_id" label="行程ID" width="90" />
      <el-table-column prop="application_id" label="申请ID" width="90" />
      <el-table-column prop="passenger_name" label="乘客" width="120" />
      <el-table-column prop="destination" label="目的地" min-width="140" />
      <el-table-column prop="distance_km" label="里程(km)" width="110" />
      <el-table-column prop="fuel_used_l" label="油耗(L)" width="100" />
      <el-table-column prop="user_rating" label="评分" width="120">
        <template #default="scope">
          <span v-if="scope.row.user_rating === null || scope.row.user_rating === undefined">未评分</span>
          <span v-else>{{ Number(scope.row.user_rating).toFixed(2) }}/5</span>
        </template>
      </el-table-column>
      <el-table-column prop="actual_end_time" label="结束时间" width="180">
        <template #default="scope">{{ formatDate(scope.row.actual_end_time) }}</template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import axios from 'axios';
import { notifyError, notifySuccess } from '../../utils/notify';
import { formatBeijingDateTime } from '../../utils/datetime';
import FractionStarDisplay from '../Common/FractionStarDisplay.vue';

const loading = ref(false);
const saving = ref(false);
const error = ref('');

const driver = ref(null);
const vehicle = ref(null);
const tasks = ref([]);
const completedTrips = ref([]);
const driverRatingAvg = ref(null);

const driverStatus = ref('available');
const vehicleStatus = ref('available');
const plateNumber = ref('');

const reportDialogVisible = ref(false);
const currentTripId = ref(null);
const reportForm = ref({
  distance_km: 0,
  fuel_used: 0
});

// 将司机/车辆/任务状态映射为标签样式
const statusType = (status) => ({
  available: 'success',
  unavailable: 'danger',
  maintenance: 'warning',
  scheduled: 'warning',
  in_progress: 'info',
  completed: 'success',
  busy: 'warning'
}[status] || 'info');

// 时间格式化显示
const formatDate = (value) => formatBeijingDateTime(value);

// 拉取司机工作台数据
const fetchDashboard = async () => {
  try {
    loading.value = true;
    const res = await axios.get('/api/drivers/me/dashboard');
    driver.value = res.data.data.driver;
    vehicle.value = res.data.data.vehicle;
    tasks.value = res.data.data.tasks || [];
    completedTrips.value = res.data.data.completed_trips || [];
    driverRatingAvg.value = res.data.data.driver_rating_avg;
    driverStatus.value = driver.value?.status || 'available';
    vehicleStatus.value = vehicle.value?.status || 'available';
  } catch (err) {
    error.value = err.response?.data?.message || '获取司机面板失败';
  } finally {
    loading.value = false;
  }
};

// 更新司机状态
const updateDriverStatus = async () => {
  try {
    saving.value = true;
    await axios.put('/api/drivers/me/status', { status: driverStatus.value });
    notifySuccess('司机状态已更新');
    await fetchDashboard();
  } catch (err) {
    error.value = err.response?.data?.message || '更新司机状态失败';
  } finally {
    saving.value = false;
  }
};

// 更新绑定车辆状态
const updateVehicleStatus = async () => {
  try {
    saving.value = true;
    await axios.put('/api/drivers/me/vehicle-status', { status: vehicleStatus.value });
    notifySuccess('车辆状态已更新');
    await fetchDashboard();
  } catch (err) {
    error.value = err.response?.data?.message || '更新车辆状态失败';
  } finally {
    saving.value = false;
  }
};

// 通过车牌号更换绑定车辆
const bindVehicle = async () => {
  try {
    saving.value = true;
    await axios.put('/api/drivers/me/bind-vehicle', { plate_number: plateNumber.value });
    notifySuccess('绑定车辆成功');
    plateNumber.value = '';
    await fetchDashboard();
  } catch (err) {
    error.value = err.response?.data?.message || '绑定车辆失败';
  } finally {
    saving.value = false;
  }
};

// 打开“司机填报”弹窗并回填历史值
const openReportDialog = (row) => {
  currentTripId.value = row.trip_id;
  reportForm.value = {
    distance_km: Number(row.driver_report_distance_km || 0),
    fuel_used: Number(row.driver_report_fuel_used_l || 0)
  };
  reportDialogVisible.value = true;
};

const pickupPassenger = async (row) => {
  try {
    if (!row?.trip_id) return;
    saving.value = true;
    await axios.post(`/api/trips/${row.trip_id}/pickup`, {});
    notifySuccess('已记录接到乘客，行程开始');
    await fetchDashboard();
  } catch (err) {
    error.value = err.response?.data?.message || '记录接乘客失败';
  } finally {
    saving.value = false;
  }
};

// 提交司机填报（里程/油量）
const submitDriverReport = async () => {
  try {
    if (!currentTripId.value) return;
    saving.value = true;
    await axios.post(`/api/trips/${currentTripId.value}/driver-report`, {
      distance_km: reportForm.value.distance_km,
      fuel_used: reportForm.value.fuel_used
    });
    notifySuccess('司机填报已保存，请通知乘客结束行程');
    reportDialogVisible.value = false;
    await fetchDashboard();
  } catch (err) {
    error.value = err.response?.data?.message || '提交填报失败';
  } finally {
    saving.value = false;
  }
};

onMounted(fetchDashboard);

watch(error, (message) => {
  if (!message) return;
  notifyError(message);
});
</script>

<style scoped>
.driver-card { max-width: 1200px; margin: 0 auto; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: 700; }
.meta-row { margin-bottom: 12px; }
.meta-title { font-weight: 700; margin: 0 0 8px; }
.mt { margin-top: 10px; }
.empty { color: #7a8770; }
</style>
