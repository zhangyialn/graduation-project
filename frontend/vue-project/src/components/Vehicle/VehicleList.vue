<template>
  <div class="vehicle-container">
    <h2>车辆管理</h2>
    <button @click="showAddForm = !showAddForm" class="btn btn-primary">
      {{ showAddForm ? '取消' : '添加车辆' }}
    </button>
    
    <!-- 添加车辆表单 -->
    <div v-if="showAddForm" class="add-form">
      <h3>添加车辆</h3>
      <form @submit.prevent="handleAddVehicle">
        <div class="form-group">
          <label for="plate_number">车牌号</label>
          <input type="text" id="plate_number" v-model="newVehicle.plate_number" required>
        </div>
        <div class="form-group">
          <label for="model">车型</label>
          <input type="text" id="model" v-model="newVehicle.model" required>
        </div>
        <div class="form-group">
          <label for="status">状态</label>
          <select id="status" v-model="newVehicle.status">
            <option value="available">可用</option>
            <option value="in_use">使用中</option>
            <option value="maintenance">维护中</option>
          </select>
        </div>
        <button type="submit" class="btn btn-success">保存</button>
      </form>
    </div>
    
    <!-- 车辆列表 -->
    <table class="table">
      <thead>
        <tr>
          <th>车辆ID</th>
          <th>车牌号</th>
          <th>车型</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="vehicle in vehicles" :key="vehicle.id">
          <td>{{ vehicle.id }}</td>
          <td>{{ vehicle.plate_number }}</td>
          <td>{{ vehicle.model }}</td>
          <td>{{ vehicle.status }}</td>
          <td>
            <button @click="editVehicle(vehicle)" class="btn btn-info">编辑</button>
            <button @click="deleteVehicle(vehicle.id)" class="btn btn-danger">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    
    <!-- 司机管理 -->
    <h3>司机管理</h3>
    <button @click="showAddDriverForm = !showAddDriverForm" class="btn btn-primary">
      {{ showAddDriverForm ? '取消' : '添加司机' }}
    </button>
    
    <!-- 添加司机表单 -->
    <div v-if="showAddDriverForm" class="add-form">
      <h4>添加司机</h4>
      <form @submit.prevent="handleAddDriver">
        <div class="form-group">
          <label for="name">姓名</label>
          <input type="text" id="name" v-model="newDriver.name" required>
        </div>
        <div class="form-group">
          <label for="license">驾驶证号</label>
          <input type="text" id="license" v-model="newDriver.license" required>
        </div>
        <div class="form-group">
          <label for="status">状态</label>
          <select id="status" v-model="newDriver.status">
            <option value="available">可用</option>
            <option value="busy">忙碌</option>
          </select>
        </div>
        <button type="submit" class="btn btn-success">保存</button>
      </form>
    </div>
    
    <!-- 司机列表 -->
    <table class="table">
      <thead>
        <tr>
          <th>司机ID</th>
          <th>姓名</th>
          <th>驾驶证号</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="driver in drivers" :key="driver.id">
          <td>{{ driver.id }}</td>
          <td>{{ driver.name }}</td>
          <td>{{ driver.license }}</td>
          <td>{{ driver.status }}</td>
          <td>
            <button @click="editDriver(driver)" class="btn btn-info">编辑</button>
            <button @click="deleteDriver(driver.id)" class="btn btn-danger">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    
    <div class="error-message" v-if="error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const vehicles = ref([]);
const drivers = ref([]);
const showAddForm = ref(false);
const showAddDriverForm = ref(false);
const error = ref('');

const newVehicle = ref({
  plate_number: '',
  model: '',
  status: 'available'
});

const newDriver = ref({
  name: '',
  license: '',
  status: 'available'
});

const fetchVehicles = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get('http://localhost:5000/api/vehicles', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    vehicles.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || '获取车辆失败';
  }
};

const fetchDrivers = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get('http://localhost:5000/api/vehicles/drivers', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    drivers.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || '获取司机失败';
  }
};

const handleAddVehicle = async () => {
  try {
    const token = localStorage.getItem('token');
    await axios.post('http://localhost:5000/api/vehicles', newVehicle.value, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    fetchVehicles();
    showAddForm.value = false;
    newVehicle.value = {
      plate_number: '',
      model: '',
      status: 'available'
    };
  } catch (err) {
    error.value = err.response?.data?.message || '添加车辆失败';
  }
};

const handleAddDriver = async () => {
  try {
    const token = localStorage.getItem('token');
    await axios.post('http://localhost:5000/api/vehicles/drivers', newDriver.value, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    fetchDrivers();
    showAddDriverForm.value = false;
    newDriver.value = {
      name: '',
      license: '',
      status: 'available'
    };
  } catch (err) {
    error.value = err.response?.data?.message || '添加司机失败';
  }
};

const editVehicle = (vehicle) => {
  // 编辑车辆逻辑
  console.log('编辑车辆:', vehicle);
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

const editDriver = (driver) => {
  // 编辑司机逻辑
  console.log('编辑司机:', driver);
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
.vehicle-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.add-form {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  margin: 1rem 0;
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

input, select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  margin: 1rem 0;
}

.table th, .table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-info {
  background-color: #17a2b8;
  color: white;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.error-message {
  margin-top: 1rem;
  color: #dc3545;
  font-size: 0.875rem;
}
</style>