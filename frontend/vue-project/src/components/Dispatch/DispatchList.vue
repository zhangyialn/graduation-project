<template>
  <div class="dispatch-container">
    <h2>调度管理</h2>
    <button @click="showAddForm = !showAddForm" class="btn btn-primary">
      {{ showAddForm ? '取消' : '添加调度' }}
    </button>
    
    <!-- 添加调度表单 -->
    <div v-if="showAddForm" class="add-form">
      <h3>添加调度</h3>
      <form @submit.prevent="handleAddDispatch">
        <div class="form-group">
          <label for="application_id">申请ID</label>
          <input type="number" id="application_id" v-model="newDispatch.application_id" required>
        </div>
        <div class="form-group">
          <label for="vehicle_id">车辆ID</label>
          <input type="number" id="vehicle_id" v-model="newDispatch.vehicle_id" required>
        </div>
        <div class="form-group">
          <label for="driver_id">司机ID</label>
          <input type="number" id="driver_id" v-model="newDispatch.driver_id" required>
        </div>
        <button type="submit" class="btn btn-success">保存</button>
      </form>
    </div>
    
    <!-- 调度列表 -->
    <table class="table">
      <thead>
        <tr>
          <th>调度ID</th>
          <th>申请ID</th>
          <th>车辆ID</th>
          <th>司机ID</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="dispatch in dispatches" :key="dispatch.id">
          <td>{{ dispatch.id }}</td>
          <td>{{ dispatch.application_id }}</td>
          <td>{{ dispatch.vehicle_id }}</td>
          <td>{{ dispatch.driver_id }}</td>
          <td>{{ dispatch.status }}</td>
          <td>
            <button @click="startDispatch(dispatch.id)" class="btn btn-success" v-if="dispatch.status === 'pending'">开始</button>
            <button @click="cancelDispatch(dispatch.id)" class="btn btn-danger">取消</button>
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

const dispatches = ref([]);
const showAddForm = ref(false);
const error = ref('');

const newDispatch = ref({
  application_id: '',
  vehicle_id: '',
  driver_id: ''
});

const fetchDispatches = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get('http://localhost:5000/api/dispatches', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    dispatches.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || '获取调度失败';
  }
};

const handleAddDispatch = async () => {
  try {
    const token = localStorage.getItem('token');
    await axios.post('http://localhost:5000/api/dispatches', newDispatch.value, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    fetchDispatches();
    showAddForm.value = false;
    newDispatch.value = {
      application_id: '',
      vehicle_id: '',
      driver_id: ''
    };
  } catch (err) {
    error.value = err.response?.data?.message || '添加调度失败';
  }
};

const startDispatch = async (id) => {
  try {
    const token = localStorage.getItem('token');
    await axios.post(`http://localhost:5000/api/dispatches/${id}/start`, {}, {
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
    await axios.post(`http://localhost:5000/api/dispatches/${id}/cancel`, {}, {
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
.dispatch-container {
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

input {
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
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-success {
  background-color: #28a745;
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
</style><template>
  <div class="dispatch-container">
    <h2>调度管理</h2>
    <button @click="showAddForm = !showAddForm" class="btn btn-primary">
      {{ showAddForm ? '取消' : '添加调度' }}
    </button>
    
    <!-- 添加调度表单 -->
    <div v-if="showAddForm" class="add-form">
      <h3>添加调度</h3>
      <form @submit.prevent="handleAddDispatch">
        <div class="form-group">
          <label for="application_id">申请ID</label>
          <input type="number" id="application_id" v-model="newDispatch.application_id" required>
        </div>
        <div class="form-group">
          <label for="vehicle_id">车辆ID</label>
          <input type="number" id="vehicle_id" v-model="newDispatch.vehicle_id" required>
        </div>
        <div class="form-group">
          <label for="driver_id">司机ID</label>
          <input type="number" id="driver_id" v-model="newDispatch.driver_id" required>
        </div>
        <button type="submit" class="btn btn-success">保存</button>
      </form>
    </div>
    
    <!-- 调度列表 -->
    <table class="table">
      <thead>
        <tr>
          <th>调度ID</th>
          <th>申请ID</th>
          <th>车辆ID</th>
          <th>司机ID</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="dispatch in dispatches" :key="dispatch.id">
          <td>{{ dispatch.id }}</td>
          <td>{{ dispatch.application_id }}</td>
          <td>{{ dispatch.vehicle_id }}</td>
          <td>{{ dispatch.driver_id }}</td>
          <td>{{ dispatch.status }}</td>
          <td>
            <button @click="startDispatch(dispatch.id)" class="btn btn-success" v-if="dispatch.status === 'pending'">开始</button>
            <button @click="cancelDispatch(dispatch.id)" class="btn btn-danger">取消</button>
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

const dispatches = ref([]);
const showAddForm = ref(false);
const error = ref('');

const newDispatch = ref({
  application_id: '',
  vehicle_id: '',
  driver_id: ''
});

const fetchDispatches = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get('http://localhost:5000/api/dispatches', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    dispatches.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || '获取调度失败';
  }
};

const handleAddDispatch = async () => {
  try {
    const token = localStorage.getItem('token');
    await axios.post('http://localhost:5000/api/dispatches', newDispatch.value, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    fetchDispatches();
    showAddForm.value = false;
    newDispatch.value = {
      application_id: '',
      vehicle_id: '',
      driver_id: ''
    };
  } catch (err) {
    error.value = err.response?.data?.message || '添加调度失败';
  }
};

const startDispatch = async (id) => {
  try {
    const token = localStorage.getItem('token');
    await axios.post(`http://localhost:5000/api/dispatches/${id}/start`, {}, {
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
    await axios.post(`http://localhost:5000/api/dispatches/${id}/cancel`, {}, {
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
.dispatch-container {
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

input {
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
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-success {
  background-color: #28a745;
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