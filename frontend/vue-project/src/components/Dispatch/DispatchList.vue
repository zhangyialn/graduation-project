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
    <el-table :data="dispatches" style="width: 100%" border>
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
          <el-button type="danger" size="small" @click="cancelDispatch(scope.row.id)">
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
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleAddDispatch" :loading="loading">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <el-alert v-if="error" :title="error" type="error" show-icon class="error-alert" />
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import axios from 'axios';
import { DataAnalysis, Plus, Check, Close } from '@element-plus/icons-vue';

const dispatches = ref([]);
const pendingApplications = ref([]);
const availableVehicles = ref([]);
const availableDrivers = ref([]);
const dialogVisible = ref(false);
const error = ref('');
const loading = ref(false);

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

const statusType = (status) => {
  const typeMap = {
    scheduled: 'warning',
    in_progress: 'info',
    completed: 'success',
    cancelled: 'danger'
  };
  return typeMap[status] || 'info';
};

const fetchDispatches = async () => {
  try {
    loading.value = true;
    const token = localStorage.getItem('token');
    const response = await axios.get('/api/dispatches', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    dispatches.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || '获取调度失败';
  } finally {
    loading.value = false;
  }
};

const openAddDialog = () => {
  form.application_id = '';
  form.vehicle_id = '';
  form.driver_id = '';
  fetchPendingApplications();
  fetchAvailableVehicles();
  fetchAvailableDrivers();
  dialogVisible.value = true;
};

const fetchPendingApplications = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get('/api/dispatches/pending', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    pendingApplications.value = response.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取待调度申请失败';
  }
};

const fetchAvailableVehicles = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get('/api/vehicles/available', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    availableVehicles.value = response.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取可用车辆失败';
  }
};

const fetchAvailableDrivers = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get('/api/vehicles/drivers/available', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    availableDrivers.value = response.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取可用司机失败';
  }
};

const handleAddDispatch = async () => {
  try {
    await dispatchForm.value.validate();
    loading.value = true;
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    const user = userStr ? JSON.parse(userStr) : null;

    if (!user) {
      error.value = '用户信息不存在';
      return;
    }

    await axios.post('/api/dispatches', {
      application_id: form.application_id,
      vehicle_id: form.vehicle_id,
      driver_id: form.driver_id,
      dispatcher_id: user.id
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    dialogVisible.value = false;
    fetchDispatches();
  } catch (err) {
    error.value = err.response?.data?.message || '添加调度失败';
  } finally {
    loading.value = false;
  }
};

const startDispatch = async (id) => {
  try {
    const token = localStorage.getItem('token');
    await axios.post(`/api/dispatches/${id}/start`, {}, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    fetchDispatches();
  } catch (err) {
    error.value = err.response?.data?.message || '开始调度失败';
  }
};

const cancelDispatch = async (id) => {
  try {
    const token = localStorage.getItem('token');
    await axios.post(`/api/dispatches/${id}/cancel`, {}, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    fetchDispatches();
  } catch (err) {
    error.value = err.response?.data?.message || '取消调度失败';
  }
};

onMounted(() => {
  fetchDispatches();
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
  background: linear-gradient(135deg, #f4f7ed 0%, #eff3e6 100%);
  padding: 1.5rem;
  border-bottom: 1px solid #e5ddd2;
}

.header-icon {
  font-size: 1.75rem;
  margin-right: 1rem;
  color: #6b8e23;
}

.card-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  flex: 1;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
  background: linear-gradient(135deg, #6b8e23 0%, #556b2f 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

:deep(.el-button.is-primary) {
  background: linear-gradient(135deg, #6b8e23 0%, #556b2f 100%) !important;
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
  background: linear-gradient(135deg, #556b2f 0%, #3d5a1f 100%) !important;
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
  background: linear-gradient(135deg, #f4f7ed 0%, #eff3e6 100%);
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