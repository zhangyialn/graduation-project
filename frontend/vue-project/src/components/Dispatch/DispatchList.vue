<!-- 调度管理页：调度列表、创建调度、智能推荐调度 -->
<template>
  <el-card class="dispatch-list-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon class="header-icon"><DataAnalysis /></el-icon>
        <h2>调度管理</h2>
        <el-button type="primary" @click="openAddDialog">
          <el-icon><Plus /></el-icon>
          添加调度
        </el-button>
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
    
    <!-- 添加调度对话框 -->
    <el-dialog v-model="dialogVisible" title="添加调度" width="400px">
      <el-form :model="form" :rules="rules" ref="dispatchForm" label-width="100px">
        <el-form-item label="申请ID" prop="application_id">
          <el-select v-model="form.application_id" placeholder="请选择待调度申请" style="width: 100%">
            <el-option
              v-for="item in pendingApplications"
              :key="item.id"
              :label="`#${item.id} - ${item.purpose}`"
              :value="item.id"
            />
          </el-select>
          <div style="margin-top: 8px;">
            <el-button plain size="small" :disabled="!form.application_id" :loading="recommending" @click="fetchDispatchRecommendation(form.application_id)">
              智能推荐调度
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="车辆ID" prop="vehicle_id">
          <el-select v-model="form.vehicle_id" placeholder="请选择可用车辆" style="width: 100%">
            <el-option
              v-for="item in availableVehicles"
              :key="item.id"
              :label="`#${item.id} - ${item.plate_number}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="司机ID" prop="driver_id">
          <el-select v-model="form.driver_id" placeholder="请选择可用司机" style="width: 100%">
            <el-option
              v-for="item in availableDrivers"
              :key="item.id"
              :label="`#${item.id} - ${item.name}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="当前油价">
          <div class="fuel-meta">{{ fuelPriceHint }}</div>
        </el-form-item>
        <el-form-item label="预估油费/km">
          <div class="fuel-meta">{{ estimatedFuelCostPerKmHint }}</div>
        </el-form-item>
        <el-form-item label="推荐说明" v-if="recommendation">
          <div class="fuel-meta">
            <div>推荐司机：{{ recommendation.driver_name }}（ID: {{ recommendation.driver_id }}）</div>
            <div>推荐车辆：{{ recommendation.plate_number }}（ID: {{ recommendation.vehicle_id }}）</div>
            <div style="margin: 6px 0;">
              <el-rate
                :model-value="normalizeRecommendationIndex(recommendation.recommendation_index)"
                disabled
                allow-half
                show-score
                score-template="{value} 分"
              />
            </div>
            <div>推荐指数：{{ normalizeRecommendationIndex(recommendation.recommendation_index).toFixed(2) }}/5</div>
            <div>{{ (recommendation.reasons || []).join('；') }}</div>
          </div>
        </el-form-item>
        <el-form-item label="Top5候选" v-if="recommendationCandidates.length > 0">
          <div style="width: 100%; display: grid; gap: 8px;">
            <el-card
              v-for="item in recommendationCandidates"
              :key="`${item.driver_id}-${item.vehicle_id}`"
              shadow="never"
              style="cursor: pointer; border: 1px solid #dfe6d2;"
              @click="applyRecommendation(item)"
            >
              <div class="fuel-meta">
                <div>
                  <strong>
                    {{ selectedRecommendationKey === `${item.driver_id}-${item.vehicle_id}` ? '已选：' : '' }}
                    司机{{ item.driver_name }} / 车辆{{ item.plate_number }}
                  </strong>
                </div>
                <div style="margin: 4px 0;">
                  <el-rate
                    :model-value="normalizeRecommendationIndex(item.recommendation_index)"
                    disabled
                    allow-half
                    show-score
                    score-template="{value} 分"
                  />
                </div>
                <div>推荐指数：{{ normalizeRecommendationIndex(item.recommendation_index).toFixed(2) }}/5，任务数：{{ item.active_dispatch_count }}</div>
                <div>{{ (item.reasons || []).join('；') }}</div>
              </div>
            </el-card>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleAddDispatch" :loading="loading">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import axios from 'axios';
import { DataAnalysis, Plus, Check, Close } from '@element-plus/icons-vue';
import { useFuelPriceStore } from '../../stores/fuelPrice';
import { useAuthStore } from '../../stores/auth';
import { notifyError, notifySuccess, notifyWarning } from '../../utils/notify';

const dispatches = ref([]);
const pendingApplications = ref([]);
const availableVehicles = ref([]);
const availableDrivers = ref([]);
const dialogVisible = ref(false);
const error = ref('');
const loading = ref(false);
const recommending = ref(false);
const recommendation = ref(null);
const recommendationCandidates = ref([]);
const selectedRecommendationKey = ref('');
const screenWidth = ref(window.innerWidth);
const isMobile = computed(() => screenWidth.value < 900);
const fuelStore = useFuelPriceStore();
const authStore = useAuthStore();

const form = reactive({
  application_id: '',
  vehicle_id: '',
  driver_id: ''
});

const rules = reactive({
  application_id: [{ required: true, message: '请输入申请ID', trigger: 'blur' }],
  vehicle_id: [{ required: true, message: '请输入车辆ID', trigger: 'blur' }],
  driver_id: [{ required: true, message: '请输入司机ID', trigger: 'blur' }]
});

const dispatchForm = ref(null);

// 规范化燃油类型，统一到油价 store 可识别的名称
const normalizeFuelType = (fuelType) => {
  const value = (fuelType || '').trim();
  if (!value) return '92号汽油';
  if (value === '汽油') return '92号汽油';
  if (value === '柴油') return '0号柴油';
  return value;
};

const selectedVehicle = computed(() => {
  if (!form.vehicle_id) return null;
  return availableVehicles.value.find(item => item.id === form.vehicle_id) || null;
});

const currentFuelType = computed(() => normalizeFuelType(selectedVehicle.value?.fuel_type));

const fuelPriceHint = computed(() => {
  if (fuelStore.currentFuelPrice === null || fuelStore.currentFuelPrice === undefined) {
    return '暂无油价（将按当日地区自动获取）';
  }
  return `${fuelStore.regionName} ${fuelStore.selectedFuelType}：${fuelStore.currentFuelPrice} 元/升`;
});

const estimatedFuelCostPerKmHint = computed(() => {
  const consumption = Number(selectedVehicle.value?.fuel_consumption_per_100km);
  const price = Number(fuelStore.currentFuelPrice);
  if (!Number.isFinite(consumption) || consumption <= 0 || !Number.isFinite(price) || price <= 0) {
    return '暂无（需车辆油耗与当日油价）';
  }
  const perKm = (consumption / 100) * price;
  return `${perKm.toFixed(2)} 元/公里`;
});

// 确保当日油价已加载，供预估油费展示
const ensureDailyFuelPrice = async (force = false) => {
  try {
    await fuelStore.fetchOilPrice({ force });
  } catch (_err) {
    if (!error.value && fuelStore.lastError) {
      error.value = `油价获取失败：${fuelStore.lastError}`;
    }
  }
};

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

const normalizeRecommendationIndex = (value) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return 0;
  return Math.max(0, Math.min(5, parsed));
};

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

// 打开新增调度弹窗，并预加载可选数据
const openAddDialog = async () => {
  form.application_id = '';
  form.vehicle_id = '';
  form.driver_id = '';
  recommendation.value = null;
  recommendationCandidates.value = [];
  selectedRecommendationKey.value = '';
  error.value = '';
  await Promise.all([
    fetchPendingApplications(),
    fetchAvailableVehicles(),
    fetchAvailableDrivers()
  ]);
  ensureDailyFuelPrice();
  dialogVisible.value = true;
};

// 拉取待调度申请
const fetchPendingApplications = async () => {
  try {
    const response = await axios.get('/api/dispatches/pending');
    pendingApplications.value = response.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取待调度申请失败';
  }
};

// 拉取可用车辆
const fetchAvailableVehicles = async () => {
  try {
    const response = await axios.get('/api/vehicles/available');
    availableVehicles.value = response.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取可用车辆失败';
  }
};

// 拉取可用司机
const fetchAvailableDrivers = async () => {
  try {
    const response = await axios.get('/api/vehicles/drivers/available');
    availableDrivers.value = response.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取可用司机失败';
  }
};

// 根据申请获取智能调度推荐
const fetchDispatchRecommendation = async (applicationId) => {
  if (!applicationId) return;
  try {
    recommending.value = true;
    const response = await axios.get(`/api/dispatches/recommend/${applicationId}`);

    const best = response.data?.data?.best;
    const candidates = response.data?.data?.candidates || [];
    recommendationCandidates.value = candidates;
    if (!best) {
      recommendation.value = null;
      selectedRecommendationKey.value = '';
      notifyWarning('未找到可调度推荐，请手动选择');
      return;
    }

    applyRecommendation(best);
    notifySuccess('已按智能推荐自动填充');
  } catch (err) {
    recommendation.value = null;
    recommendationCandidates.value = [];
    selectedRecommendationKey.value = '';
    error.value = err.response?.data?.message || '获取智能推荐失败';
  } finally {
    recommending.value = false;
  }
};

// 应用推荐结果到表单
const applyRecommendation = (candidate) => {
  if (!candidate) return;
  recommendation.value = candidate;
  selectedRecommendationKey.value = `${candidate.driver_id}-${candidate.vehicle_id}`;
  form.driver_id = candidate.driver_id;
  form.vehicle_id = candidate.vehicle_id;
};

// 提交新增调度
const handleAddDispatch = async () => {
  try {
    await dispatchForm.value.validate();
    loading.value = true;
    const user = authStore.user;

    if (!user) {
      error.value = '用户信息不存在';
      return;
    }

    await axios.post('/api/dispatches', {
      application_id: form.application_id,
      vehicle_id: form.vehicle_id,
      driver_id: form.driver_id,
      dispatcher_id: user.id
    });
    dialogVisible.value = false;
    await fetchDispatches();
  } catch (err) {
    error.value = err.response?.data?.message || '添加调度失败';
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
  fuelStore.initializeDailyOilPrice().catch(() => null);
  window.addEventListener('resize', updateWidth);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateWidth);
});

watch(() => form.vehicle_id, async () => {
  if (!selectedVehicle.value) return;
  fuelStore.setFuelType(currentFuelType.value);
  await ensureDailyFuelPrice();
});

watch(() => form.application_id, async (applicationId) => {
  if (!dialogVisible.value || !applicationId) return;
  await fetchDispatchRecommendation(applicationId);
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
