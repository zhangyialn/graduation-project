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
        <el-table-column prop="license" label="驾驶证号" />
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
  status: 'available'
});

const vehicleRules = reactive({
  plate_number: [{ required: true, message: '请输入车牌号', trigger: 'blur' }],
  model: [{ required: true, message: '请输入车型', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
});

const driverForm = reactive({
  id: null,
  name: '',
  license: '',
  status: 'available'
});

const driverRules = reactive({
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  license: [{ required: true, message: '请输入驾驶证号', trigger: 'blur' }],
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
    const response = await axios.get('http://localhost:5000/api/vehicles', {
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
    const response = await axios.get('http://localhost:5000/api/vehicles/drivers', {
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
    vehicleDialogTitle.value = '编辑车辆';
  } else {
    vehicleForm.id = null;
    vehicleForm.plate_number = '';
    vehicleForm.model = '';
    vehicleForm.status = 'available';
    vehicleDialogTitle.value = '添加车辆';
  }
  vehicleDialogVisible.value = true;
};

const openDriverDialog = (driver = null) => {
  if (driver) {
    driverForm.id = driver.id;
    driverForm.name = driver.name;
    driverForm.license = driver.license;
    driverForm.status = driver.status;
    driverDialogTitle.value = '编辑司机';
  } else {
    driverForm.id = null;
    driverForm.name = '';
    driverForm.license = '';
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
    if (vehicleForm.id) {
      // 编辑车辆
      await axios.put(`http://localhost:5000/api/vehicles/${vehicleForm.id}`, vehicleForm, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
    } else {
      // 添加车辆
      await axios.post('http://localhost:5000/api/vehicles', vehicleForm, {
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
    if (driverForm.id) {
      // 编辑司机
      await axios.put(`http://localhost:5000/api/vehicles/drivers/${driverForm.id}`, driverForm, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
    } else {
      // 添加司机
      await axios.post('http://localhost:5000/api/vehicles/drivers', driverForm, {
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
    await axios.delete(`http://localhost:5000/api/vehicles/${id}`, {
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
    await axios.delete(`http://localhost:5000/api/vehicles/drivers/${id}`, {
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
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-icon {
  font-size: 1.5rem;
  margin-right: 0.75rem;
  color: #409EFF;
}

.card-header h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  flex: 1;
}

.driver-section {
  margin-top: 2rem;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.section-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  flex: 1;
  display: flex;
  align-items: center;
}

.section-header .header-icon {
  margin-right: 0.5rem;
}

.error-alert {
  margin-top: 1rem;
}
</style>