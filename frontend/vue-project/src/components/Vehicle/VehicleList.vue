<template>
  <el-card class="vehicle-list-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon class="header-icon"><Van /></el-icon>
        <h2>车辆管理</h2>
        <el-button type="primary" @click="openVehicleDialog">
          <el-icon><Plus /></el-icon>
          添加车辆
        </el-button>
      </div>
    </template>
    
    <!-- 车辆列表 -->
    <el-table :data="vehicles" style="width: 100%" border>
      <el-table-column prop="id" label="车辆ID" width="80" />
      <el-table-column prop="plate_number" label="车牌号" width="120" />
      <el-table-column prop="model" label="车型" width="120" />
      <el-table-column prop="fuel_type" label="油品型号" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="vehicleStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="scope">
          <el-button type="primary" size="small" @click="openVehicleDialog(scope.row)">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button type="danger" size="small" @click="deleteVehicle(scope.row.id)">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 车辆对话框 -->
    <el-dialog v-model="vehicleDialogVisible" :title="vehicleDialogTitle" width="400px">
      <el-form :model="vehicleForm" :rules="vehicleRules" ref="vehicleFormRef" label-width="100px">
        <el-form-item label="车牌号" prop="plate_number">
          <el-input v-model="vehicleForm.plate_number" placeholder="请输入车牌号" />
        </el-form-item>
        <el-form-item label="车型" prop="model">
          <el-input v-model="vehicleForm.model" placeholder="请输入车型" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="vehicleForm.status" placeholder="请选择状态">
            <el-option label="可用" value="available" />
            <el-option label="使用中" value="in_use" />
            <el-option label="维护中" value="maintenance" />
          </el-select>
        </el-form-item>
        <el-form-item label="油品型号" prop="fuel_type">
          <el-select v-model="vehicleForm.fuel_type" placeholder="请选择油品型号">
            <el-option label="92号汽油" value="92号汽油" />
            <el-option label="95号汽油" value="95号汽油" />
            <el-option label="98号汽油" value="98号汽油" />
            <el-option label="0号柴油" value="0号柴油" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="vehicleDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveVehicle" :loading="loading">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 司机管理 -->
    <div class="driver-section">
      <div class="section-header">
        <el-icon class="header-icon"><UserFilled /></el-icon>
        <h3>司机管理</h3>
        <el-button type="primary" @click="openDriverDialog">
          <el-icon><Plus /></el-icon>
          添加司机
        </el-button>
      </div>
      
      <!-- 司机列表 -->
      <el-table :data="drivers" style="width: 100%" border>
        <el-table-column prop="id" label="司机ID" width="80" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="license_number" label="驾驶证号" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="driverStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button type="primary" size="small" @click="openDriverDialog(scope.row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="deleteDriver(scope.row.id)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 司机对话框 -->
    <el-dialog v-model="driverDialogVisible" :title="driverDialogTitle" width="400px">
      <el-form :model="driverForm" :rules="driverRules" ref="driverFormRef" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="driverForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="驾驶证号" prop="license">
          <el-input v-model="driverForm.license" placeholder="请输入驾驶证号" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="driverForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="driverForm.status" placeholder="请选择状态">
            <el-option label="可用" value="available" />
            <el-option label="忙碌" value="busy" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="driverDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveDriver" :loading="loading">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <el-alert v-if="error" :title="error" type="error" show-icon class="error-alert" />
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import axios from 'axios';
import { Van, Plus, Edit, Delete, UserFilled } from '@element-plus/icons-vue';

const vehicles = ref([]);
const drivers = ref([]);
const vehicleDialogVisible = ref(false);
const driverDialogVisible = ref(false);
const vehicleDialogTitle = ref('添加车辆');
const driverDialogTitle = ref('添加司机');
const error = ref('');
const loading = ref(false);

const vehicleForm = reactive({
  id: null,
  plate_number: '',
  model: '',
  status: 'available',
  brand: '',
  color: '',
  fuel_type: '92号汽油',
  seat_count: 5,
  purchase_date: '',
  fuel_consumption_per_100km: null
});

const vehicleRules = reactive({
  plate_number: [{ required: true, message: '请输入车牌号', trigger: 'blur' }],
  model: [{ required: true, message: '请输入车型', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
  fuel_type: [{ required: true, message: '请选择油品型号', trigger: 'change' }]
});

const driverForm = reactive({
  id: null,
  name: '',
  license: '',
  phone: '',
  status: 'available'
});

const driverRules = reactive({
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  license: [{ required: true, message: '请输入驾驶证号', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
});

const vehicleFormRef = ref(null);
const driverFormRef = ref(null);

const vehicleStatusType = (status) => {
  const typeMap = {
    available: 'success',
    in_use: 'warning',
    maintenance: 'info'
  };
  return typeMap[status] || 'info';
};

const driverStatusType = (status) => {
  const typeMap = {
    available: 'success',
    busy: 'warning'
  };
  return typeMap[status] || 'info';
};

const fetchVehicles = async () => {
  try {
    loading.value = true;
    const token = localStorage.getItem('token');
    const response = await axios.get('/api/vehicles', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    vehicles.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || '获取车辆失败';
  } finally {
    loading.value = false;
  }
};

const fetchDrivers = async () => {
  try {
    loading.value = true;
    const token = localStorage.getItem('token');
    const response = await axios.get('/api/vehicles/drivers', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    drivers.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || '获取司机失败';
  } finally {
    loading.value = false;
  }
};

const openVehicleDialog = (vehicle = null) => {
  if (vehicle) {
    vehicleForm.id = vehicle.id;
    vehicleForm.plate_number = vehicle.plate_number;
    vehicleForm.model = vehicle.model;
    vehicleForm.status = vehicle.status;
    vehicleForm.brand = vehicle.brand;
    vehicleForm.color = vehicle.color;
    vehicleForm.fuel_type = vehicle.fuel_type;
    vehicleForm.seat_count = vehicle.seat_count;
    vehicleForm.purchase_date = vehicle.purchase_date;
    vehicleForm.fuel_consumption_per_100km = vehicle.fuel_consumption_per_100km;
    vehicleDialogTitle.value = '编辑车辆';
  } else {
    vehicleForm.id = null;
    vehicleForm.plate_number = '';
    vehicleForm.model = '';
    vehicleForm.status = 'available';
    vehicleForm.brand = '';
    vehicleForm.color = '';
    vehicleForm.fuel_type = '92号汽油';
    vehicleForm.seat_count = 5;
    vehicleForm.purchase_date = '';
    vehicleForm.fuel_consumption_per_100km = null;
    vehicleDialogTitle.value = '添加车辆';
  }
  vehicleDialogVisible.value = true;
};

const openDriverDialog = (driver = null) => {
  if (driver) {
    driverForm.id = driver.id;
    driverForm.name = driver.name;
    driverForm.license = driver.license_number;
    driverForm.phone = driver.phone;
    driverForm.status = driver.status;
    driverDialogTitle.value = '编辑司机';
  } else {
    driverForm.id = null;
    driverForm.name = '';
    driverForm.license = '';
    driverForm.phone = '';
    driverForm.status = 'available';
    driverDialogTitle.value = '添加司机';
  }
  driverDialogVisible.value = true;
};

const saveVehicle = async () => {
  try {
    await vehicleFormRef.value.validate();
    loading.value = true;
    const token = localStorage.getItem('token');
    const vehiclePayload = {
      plate_number: vehicleForm.plate_number,
      model: vehicleForm.model,
      status: vehicleForm.status,
      brand: vehicleForm.brand || vehicleForm.model || '未知品牌',
      color: vehicleForm.color || '未填写',
      purchase_date: vehicleForm.purchase_date || new Date().toISOString().slice(0, 10),
      fuel_type: vehicleForm.fuel_type || '92号汽油',
      seat_count: vehicleForm.seat_count || 5,
      fuel_consumption_per_100km: vehicleForm.fuel_consumption_per_100km
    };
    if (vehicleForm.id) {
      // 编辑车辆
      await axios.put(`/api/vehicles/${vehicleForm.id}`, vehiclePayload, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
    } else {
      // 添加车辆
      await axios.post('/api/vehicles', vehiclePayload, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
    }
    vehicleDialogVisible.value = false;
    fetchVehicles();
  } catch (err) {
    error.value = err.response?.data?.message || '保存失败';
  } finally {
    loading.value = false;
  }
};

const saveDriver = async () => {
  try {
    await driverFormRef.value.validate();
    loading.value = true;
    const token = localStorage.getItem('token');
    const driverPayload = {
      name: driverForm.name,
      phone: driverForm.phone,
      license_number: driverForm.license,
      status: driverForm.status
    };
    if (driverForm.id) {
      // 编辑司机
      await axios.put(`/api/vehicles/drivers/${driverForm.id}`, driverPayload, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
    } else {
      // 添加司机
      await axios.post('/api/vehicles/drivers', driverPayload, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
    }
    driverDialogVisible.value = false;
    fetchDrivers();
  } catch (err) {
    error.value = err.response?.data?.message || '保存失败';
  } finally {
    loading.value = false;
  }
};

const deleteVehicle = async (id) => {
  try {
    const token = localStorage.getItem('token');
    await axios.delete(`/api/vehicles/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    fetchVehicles();
  } catch (err) {
    error.value = err.response?.data?.message || '删除车辆失败';
  }
};

const deleteDriver = async (id) => {
  try {
    const token = localStorage.getItem('token');
    await axios.delete(`/api/vehicles/drivers/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    fetchDrivers();
  } catch (err) {
    error.value = err.response?.data?.message || '删除司机失败';
  }
};

onMounted(() => {
  fetchVehicles();
  fetchDrivers();
});
</script>

<style scoped>
.vehicle-list-card {
  max-width: 1200px;
  margin: 0 auto;
  border-radius: 12px;
  border: 1px solid #e5ddd2;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
  background-color: #ffffff;
}

.vehicle-list-card:hover {
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

:deep(.el-tag.is-info) {
  background-color: #dbeafe;
  color: #1e40af;
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

:deep(.el-select__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  border-radius: 6px;
}

:deep(.el-button.is-primary) {
  background-color: #6b8e23 !important;
  border-color: #6b8e23 !important;
  border-radius: 6px !important;
  color: #ffffff !important;
  font-weight: 600 !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
  height: 40px !important;
}

:deep(.el-button[type="primary"]) {
  background: linear-gradient(135deg, #6b8e23 0%, #556b2f 100%) !important;
  border: none !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
  color: #ffffff !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
  height: 40px !important;
}

:deep(.el-button[type="primary"]:hover) {
  box-shadow: 0 8px 20px rgba(107, 142, 35, 0.3) !important;
  transform: translateY(-2px);
  background: linear-gradient(135deg, #556b2f 0%, #3d5a1f 100%) !important;
}

:deep(.el-button--danger) {
  background-color: #fee2e2 !important;
  border: 1px solid #fecaca !important;
  color: #dc2626 !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-button--danger:hover) {
  background-color: #fca5a5 !important;
  border-color: #fca5a5 !important;
  color: #991b1b !important;
}

.driver-section {
  margin-top: 2.5rem;
  padding-top: 2rem;
  border-top: 1px solid #e5ddd2;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  padding: 0 0 1rem 0;
  border-bottom: 1px solid #e5ddd2;
}

.section-header h3 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  flex: 1;
  display: flex;
  align-items: center;
  color: #2d3436;
}

.section-header .header-icon {
  margin-right: 0.75rem;
  font-size: 1.5rem;
  color: #6b8e23;
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