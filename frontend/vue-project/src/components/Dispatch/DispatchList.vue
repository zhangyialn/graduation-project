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
          <el-button type="success" size="small" @click="startDispatch(scope.row.id)" v-if="scope.row.status === 'pending'">
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
          <el-input v-model.number="form.application_id" placeholder="请输入申请ID" />
        </el-form-item>
        <el-form-item label="车辆ID" prop="vehicle_id">
          <el-input v-model.number="form.vehicle_id" placeholder="请输入车辆ID" />
        </el-form-item>
        <el-form-item label="司机ID" prop="driver_id">
          <el-input v-model.number="form.driver_id" placeholder="请输入司机ID" />
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
    pending: 'warning',
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
    const response = await axios.get('http://localhost:5000/api/dispatches', {
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
  dialogVisible.value = true;
};

const handleAddDispatch = async () => {
  try {
    await dispatchForm.value.validate();
    loading.value = true;
    const token = localStorage.getItem('token');
    await axios.post('http://localhost:5000/api/dispatches', form, {
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
.dispatch-list-card {
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

.error-alert {
  margin-top: 1rem;
}
</style>