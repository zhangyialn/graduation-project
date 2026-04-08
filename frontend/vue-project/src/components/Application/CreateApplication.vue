<!-- 用车申请创建页：支持定位起点、地址标准化、司机选择与提交 -->
<template>
  <el-card class="application-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon class="header-icon"><DocumentAdd /></el-icon>
        <h2>用车申请</h2>
      </div>
    </template>
    <el-form :model="form" :rules="rules" ref="applicationForm" label-width="120px">
      <el-form-item label="部门(ID)" prop="department_id">
        <el-input v-model="form.department_label" disabled placeholder="当前用户所属部门" />
      </el-form-item>
      <el-form-item label="用车事由" prop="purpose">
        <el-input v-model="form.purpose" placeholder="请输入用车事由" />
      </el-form-item>
      <el-form-item label="开始时间" prop="start_time">
        <el-date-picker
          v-model="form.start_time"
          type="datetime"
          placeholder="选择开始时间"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="目的地" prop="destination">
        <el-input v-model="form.destination" placeholder="请输入目的地" />
        <div style="margin-top: 8px; display: flex; gap: 8px;">
          <el-button plain size="small" @click="normalizeAddressField('destination')" :loading="normalizingDestination">标准化目的地</el-button>
        </div>
      </el-form-item>
      <el-form-item label="起点" prop="start_point">
        <el-input v-model="form.start_point" :placeholder="locating ? '定位中...' : '请输入起点（可由审批员二次调整）'" />
        <div style="margin-top: 8px; display: flex; gap: 8px;">
          <el-button plain size="small" @click="fillStartPointByLocation" :loading="locating">定位当前位置</el-button>
          <el-button plain size="small" @click="normalizeAddressField('start_point')" :loading="normalizingStartPoint">标准化起点</el-button>
        </div>
      </el-form-item>
      <el-form-item label="司机" prop="driver_id">
        <div style="width: 100%; display: grid; gap: 10px;">
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <el-button
              plain
              size="small"
              :loading="recommendingDrivers"
              @click="fetchRecommendedDrivers"
            >智能推荐司机</el-button>
            <span class="recommend-tip" v-if="recommendedDrivers.length > 0">已按推荐指数降序展示前5候选</span>
          </div>

          <div v-if="recommendedDrivers.length > 0" class="recommendation-list">
            <el-card
              v-for="item in recommendedDrivers"
              :key="`${item.driver_id}-${item.vehicle_id}`"
              shadow="never"
              class="recommendation-item"
              @click="applyRecommendedDriver(item)"
            >
              <div class="recommendation-title">
                <strong>{{ item.driver_name }}</strong>
                <span>车辆 {{ item.plate_number }}</span>
              </div>
              <div class="recommendation-rate">
                <el-rate
                  :model-value="Number(item.recommendation_index || 0)"
                  disabled
                  allow-half
                  show-score
                  score-template="{value} 分"
                />
                <el-tag size="small" type="success">推荐指数 {{ Number(item.recommendation_index || 0).toFixed(2) }}/5</el-tag>
              </div>
              <div class="recommendation-desc">{{ (item.reasons || []).join('；') }}</div>
            </el-card>
          </div>

          <el-select v-model="form.driver_id" placeholder="请选择可用司机" style="width: 100%">
            <el-option
              v-for="item in recommendedDrivers"
              :key="`rec-${item.driver_id}`"
              :label="`[推荐 ${Number(item.recommendation_index || 0).toFixed(2)}/5] ${item.driver_name}（${item.plate_number || '未绑定车牌'}）`"
              :value="item.driver_id"
            />
            <el-option
              v-for="item in nonRecommendedDrivers"
              :key="item.id"
              :label="`${item.name}（${item.vehicle_plate_number || '未绑定车牌'}）`"
              :value="item.id"
            />
          </el-select>
        </div>
      </el-form-item>
      <el-form-item label="乘车人数" prop="passenger_count">
        <el-input-number v-model="form.passenger_count" :min="1" :max="10" placeholder="请输入乘车人数" />
      </el-form-item>
      <el-form-item class="form-actions">
        <el-button class="action-btn" type="primary" @click="handleSubmit" :loading="loading">提交申请</el-button>
        <el-button class="action-btn" @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, reactive, watch, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { DocumentAdd } from '@element-plus/icons-vue';
import { useAuthStore } from '../../stores/auth';
import { notifyError, notifySuccess, notifyWarning } from '../../utils/notify';

const router = useRouter();
const authStore = useAuthStore();
const form = reactive({
  department_id: null,
  department_label: '',
  purpose: '',
  start_time: '',
  start_point: '',
  driver_id: '',
  destination: '',
  passenger_count: 1
});
const availableDrivers = ref([]);
const recommendedDrivers = ref([]);
const departments = ref([]);
const rules = reactive({
  department_id: [{ required: true, message: '用户部门缺失，请联系管理员', trigger: 'change' }],
  purpose: [{ required: true, message: '请输入用车事由', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  start_point: [{ required: true, message: '请输入起点', trigger: 'blur' }],
  driver_id: [{ required: true, message: '请选择司机', trigger: 'change' }],
  destination: [{ required: true, message: '请输入目的地', trigger: 'blur' }],
  passenger_count: [{ required: true, message: '请输入乘车人数', trigger: 'blur' }]
});
const error = ref('');
const success = ref('');
const loading = ref(false);
const recommendingDrivers = ref(false);
const locating = ref(false);
const normalizingStartPoint = ref(false);
const normalizingDestination = ref(false);
const applicationForm = ref(null);

const nonRecommendedDrivers = computed(() => {
  const recommendedIds = new Set(recommendedDrivers.value.map(item => Number(item.driver_id)));
  return availableDrivers.value.filter(item => !recommendedIds.has(Number(item.id)));
});

// 设置错误消息（并清空成功消息）
const setError = (message) => {
  error.value = message || '';
  if (message) {
    success.value = '';
  }
};

// 设置成功消息（并清空错误消息）
const setSuccess = (message) => {
  success.value = message || '';
  if (message) {
    error.value = '';
  }
};

// 拉取当前可分配司机列表
const fetchAvailableDrivers = async () => {
  const response = await axios.get('/api/vehicles/drivers/available');
  availableDrivers.value = response.data?.data || [];
};

// 拉取推荐司机（按评分/经验/座位/目的地历史综合排序）
const fetchRecommendedDrivers = async () => {
  try {
    recommendingDrivers.value = true;
    const params = {
      passenger_count: Number(form.passenger_count) || 1,
      destination: (form.destination || '').trim()
    };
    const response = await axios.get('/api/applications/recommend-drivers', { params });
    const rows = response.data?.data || [];
    recommendedDrivers.value = rows.slice(0, 5);
    if (!recommendedDrivers.value.length) {
      notifyWarning('暂无可推荐司机，请手动选择');
    }
  } catch (err) {
    notifyWarning(err.response?.data?.message || '获取推荐司机失败，请手动选择');
  } finally {
    recommendingDrivers.value = false;
  }
};

// 选择推荐司机后回填 driver_id
const applyRecommendedDriver = (item) => {
  if (!item?.driver_id) return;
  form.driver_id = item.driver_id;
};

const fetchDepartments = async () => {
  const response = await axios.get('/api/users/departments');
  departments.value = response.data?.data || [];
  console.log('Fetched departments:', departments.value);
};

const refreshCurrentUser = async () => {
  try {
    const response = await axios.get('/api/auth/me');
    const latestUser = response.data?.data;
    if (latestUser) {
      authStore.setUser(latestUser);
      return true;
    }
    return false;
  } catch (_err) {
    return false;
  }
};

const syncDepartmentFromCurrentUser = () => {
  const user = authStore.user;
  const departmentId = user?.department_id;
  if ([null, undefined, '', 0, '0'].includes(departmentId)) {
    form.department_id = null;
    form.department_label = '';
    return false;
  }

  form.department_id = Number(departmentId);
  const currentDepartment = departments.value.find(item => Number(item.id) === Number(departmentId));
  const departmentName = currentDepartment?.name || '未知部门';
  form.department_label = `${departmentName}（${departmentId}）`;
  return true;
};

// 统一坐标精度，避免提交过长小数
const formatCoordinate = (value) => {
  const number = Number(value);
  if (!Number.isFinite(number)) return '';
  return number.toFixed(6);
};

// 将逆地理结果拼装为更符合中文阅读习惯的地址文本
const buildAddressText = (address = {}) => {
  const province = address.state || address.province || '';
  const city = address.city || address.town || address.county || address.state_district || '';
  const district = address.city_district || address.suburb || address.borough || address.quarter || '';
  const road = address.road || address.pedestrian || address.residential || address.neighbourhood || '';
  const number = address.house_number || '';

  const parts = [province, city, district, road, number].filter(Boolean);
  return parts.join('');
};

// 调用地理服务把经纬度转换为地址
const reverseGeocode = async (lat, lng) => {
  const query = new URLSearchParams({
    format: 'jsonv2',
    lat: String(lat),
    lon: String(lng),
    'accept-language': 'zh-CN',
    addressdetails: '1'
  });

  const response = await fetch(`https://nominatim.openstreetmap.org/reverse?${query.toString()}`);
  if (!response.ok) {
    throw new Error('地址解析失败');
  }
  const result = await response.json();
  const addressText = buildAddressText(result.address || {});
  if (addressText) return addressText;
  return result.display_name || '';
};

// 获取浏览器定位结果
const getCurrentPosition = () => new Promise((resolve, reject) => {
  if (!navigator.geolocation) {
    reject(new Error('当前浏览器不支持定位'));
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (position) => resolve(position),
    (geoError) => reject(geoError),
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0
    }
  );
});

// 用定位结果自动回填起点；解析地址失败时降级为坐标描述
const fillStartPointByLocation = async () => {
  try {
    locating.value = true;
    const position = await getCurrentPosition();
    const lat = formatCoordinate(position.coords.latitude);
    const lng = formatCoordinate(position.coords.longitude);
    if (!lat || !lng) {
      notifyWarning('定位结果异常，请手动填写起点');
      return;
    }
    try {
      const addressText = await reverseGeocode(lat, lng);
      if (addressText) {
        form.start_point = addressText;
        return;
      }
    } catch (_reverseErr) {
      // 地址服务不可用时，降级为坐标
    }

    form.start_point = `重庆市渝中区附近（纬度:${lat}，经度:${lng}）`;
    notifyWarning('未能解析精确地址，已回填定位坐标，可手动修改');
  } catch (_err) {
    notifyWarning('定位失败，请检查浏览器定位权限后重试，或手动填写起点');
  } finally {
    locating.value = false;
  }
};

// 调用后端地址标准化接口，提升审批与调度的一致性
const normalizeAddressField = async (fieldName) => {
  const value = (form[fieldName] || '').trim();
  if (!value) {
    notifyWarning('请先输入地址再标准化');
    return;
  }

  const loadingRef = fieldName === 'start_point' ? normalizingStartPoint : normalizingDestination;
  try {
    loadingRef.value = true;
    const response = await axios.post('/api/applications/normalize-address', {
      text: value
    });
    const normalizedText = response.data?.data?.normalized_text;
    if (normalizedText) {
      form[fieldName] = normalizedText;
      notifySuccess('地址标准化完成');
    }
  } catch (err) {
    notifyWarning(err.response?.data?.message || '地址标准化失败，已保留原值');
  } finally {
    loadingRef.value = false;
  }
};

// 校验并提交申请：提交前尝试标准化起点和目的地
const handleSubmit = async () => {
  try {
    await applicationForm.value.validate();
    loading.value = true;
    setError('');
    setSuccess('');
    const refreshed = await refreshCurrentUser();
    if (refreshed) {
      syncDepartmentFromCurrentUser();
    }
    const user = authStore.user;
    if (!user) {
      setError('用户信息不存在');
      return;
    }

    if (form.start_point) {
      await normalizeAddressField('start_point');
    }
    if (form.destination) {
      await normalizeAddressField('destination');
    }

    const payload = {
      applicant_id: user.id,
      department_id: form.department_id,
      driver_id: form.driver_id,
      purpose: form.purpose,
      start_point: form.start_point,
      destination: form.destination,
      passenger_count: form.passenger_count,
      start_time: form.start_time ? new Date(form.start_time).toISOString() : ''
    };

    await axios.post('/api/applications', payload);
    setSuccess('申请提交成功');
    setTimeout(() => {
      router.push('/dashboard/applications');
    }, 2000);
  } catch (err) {
    setError(err.response?.data?.message || '提交失败');
  } finally {
    loading.value = false;
  }
};

// 重置表单输入
const resetForm = () => {
  form.purpose = '';
  form.start_time = '';
  form.start_point = '';
  form.driver_id = '';
  form.destination = '';
  form.passenger_count = 1;
  applicationForm.value?.clearValidate();
};

onMounted(async () => {
  try {
    authStore.hydrate();
    const refreshed = await refreshCurrentUser();
    if (!refreshed) {
      setError('获取当前用户信息失败，请重新登录后重试');
      return;
    }
    await fetchDepartments();
    const synced = syncDepartmentFromCurrentUser();
    console.log('Department sync status:', synced, 'Current department_id:', form.department_id);
    if (!synced) {
      setError('当前账号未配置部门，无法提交用车申请，请联系管理员设置所属部门');
      return;
    }
    await fetchAvailableDrivers();
    if (form.destination || form.passenger_count) {
      await fetchRecommendedDrivers();
    }
    if (!form.start_point) {
      await fillStartPointByLocation();
    }
  } catch (err) {
    setError(err.response?.data?.message || '获取可用司机失败');
  }
});

watch(error, (message) => {
  if (!message) return;
  notifyError(message);
});

watch(success, (message) => {
  if (!message) return;
  notifySuccess(message);
});

watch(() => [form.destination, form.passenger_count], async ([destination, passengerCount]) => {
  if (!(destination || '').trim() || !passengerCount) return;
  await fetchRecommendedDrivers();
});
</script>

<style scoped>
.application-card {
  max-width: 900px;
  margin: 0 auto;
  border-radius: 12px;
  border: 1px solid #e5ddd2;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
  background-color: #ffffff;
}

@media (max-width: 768px) {
  .application-card {
    border-radius: 10px;
  }

  :deep(.el-card__body) {
    padding: 14px;
  }

  :deep(.el-form-item__label) {
    line-height: 1.3;
  }

  :deep(.form-actions .el-form-item__content) {
    flex-direction: column;
    align-items: stretch;
  }

  .action-btn {
    width: 100% !important;
  }
}

.application-card:hover {
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

:deep(.el-card__body) {
  padding: 2rem;
  background-color: #ffffff;
}

:deep(.el-form-item) {
  margin-bottom: 22px;
}

:deep(.el-form-item__label) {
  color: #2d3436;
  font-weight: 600;
  font-size: 0.95rem;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
}

:deep(.el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  border-radius: 8px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.03);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #d4c5b9;
  background-color: #ffffff;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05), 0 0 0 3px rgba(107, 142, 35, 0.1);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #6b8e23;
  background-color: #ffffff;
  box-shadow: 0 0 0 3px rgba(107, 142, 35, 0.15);
  outline: none;
}

:deep(.el-input__prefix) {
  color: #8b7355;
}

:deep(.el-input-number .el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  border-radius: 8px;
}

:deep(.el-date-editor) {
  width: 100%;
}

:deep(.el-date-editor .el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  border-radius: 8px;
}

:deep(.el-button.is-primary) {
  height: 40px !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
  background: #5f7f24 !important;
  border: none !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
  margin-right: 0.75rem;
  color: #ffffff !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-button.is-primary:hover) {
  box-shadow: 0 8px 20px rgba(107, 142, 35, 0.3) !important;
  transform: translateY(-2px);
  background: #4f6c1f !important;
}

:deep(.el-button:not(.is-primary)) {
  height: 40px !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
  background-color: #f0f3eb !important;
  border: 1px solid #d4dcc9 !important;
  color: #6b8e23 !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

.recommend-tip {
  color: #6b8e23;
  font-size: 12px;
  line-height: 24px;
}

.recommendation-list {
  display: grid;
  gap: 8px;
}

.recommendation-item {
  border: 1px solid #dfe6d2;
  cursor: pointer;
}

.recommendation-title {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
  color: #2d3436;
}

.recommendation-rate {
  margin-top: 6px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.recommendation-desc {
  margin-top: 6px;
  color: #4d5b44;
  font-size: 12px;
}

:deep(.el-button:not(.is-primary):hover) {
  background-color: #e5edd8 !important;
  border-color: #c5cdb6 !important;
  color: #556b2f !important;
  transform: translateY(-2px);
}

:deep(.form-actions .el-form-item__content) {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap;
}

.action-btn {
  width: 140px !important;
  margin-right: 0 !important;
}

.error-alert {
  margin-top: 1.5rem;
  border-radius: 8px;
  border: 1px solid #fde2e4;
  background-color: #fef0f0;
  animation: slideDown 0.3s ease;
}

.success-alert {
  margin-top: 1.5rem;
  border-radius: 8px;
  border: 1px solid #c6e2ff;
  background-color: #f0f9ff;
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
</style>
