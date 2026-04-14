<!-- UserImport：管理员导入普通用户与审批员（单个/批量） -->
<template>
  <div class="page">
    <el-card shadow="hover" class="card">
      <template #header>
        <div class="card-header">
          <div>
            <div class="title">用户导入功能</div>
            <div class="hint">支持单个导入与Excel批量导入，支持普通用户/审批员/司机；部门为必填，支持创建部门、修改部门名称及替换负责人</div>
          </div>
        </div>
      </template>

      <el-card shadow="never" class="department-card">
        <div class="department-title">部门管理</div>
        <el-form :model="departmentForm" :rules="departmentRules" ref="departmentFormRef" inline class="department-form-row" :show-message="false">
          <el-form-item label="部门名称" prop="name" class="department-form-item">
            <el-input v-model="departmentForm.name" placeholder="请输入部门名称" style="width: 220px" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" plain :loading="creatingDepartment" @click="submitDepartment">创建部门</el-button>
          </el-form-item>
        </el-form>
        <el-form :model="departmentRenameForm" :rules="departmentRenameRules" ref="departmentRenameFormRef" inline class="department-form-row" :show-message="false">
          <el-form-item label="选择部门" prop="department_id" class="department-form-item">
            <el-select v-model="departmentRenameForm.department_id" placeholder="请选择部门" style="width: 220px">
              <el-option
                v-for="item in departments"
                :key="item.id"
                :label="`${item.id} - ${item.name}`"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="部门名称" prop="name" class="department-form-item">
            <el-input v-model="departmentRenameForm.name" placeholder="请输入新的部门名称" style="width: 220px" />
          </el-form-item>
          <el-form-item>
            <el-button type="success" plain :loading="savingDepartmentName" @click="submitDepartmentRename">保存部门名称</el-button>
          </el-form-item>
        </el-form>
        <el-form :model="leaderReplaceForm" :rules="leaderReplaceRules" ref="leaderReplaceFormRef" inline class="department-form-row" :show-message="false">
          <el-form-item label="选择部门" prop="department_id" class="department-form-item">
            <el-select v-model="leaderReplaceForm.department_id" placeholder="请选择部门" style="width: 220px">
              <el-option
                v-for="item in departments"
                :key="item.id"
                :label="`${item.id} - ${item.name}`"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="负责人（管理员）" prop="leader_id" class="department-form-item">
            <el-select v-model="leaderReplaceForm.leader_id" placeholder="请选择新的负责人" style="width: 300px">
              <el-option
                v-for="item in adminOptions"
                :key="item.id"
                :label="item.label"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="warning" plain :loading="replacingLeader" @click="submitReplaceLeader">更换负责人</el-button>
          </el-form-item>
        </el-form>
        <div class="department-list">当前部门：{{ departmentSummary }}</div>
      </el-card>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="单个导入" name="single">
          <el-form :model="singleForm" :rules="singleRules" ref="singleFormRef" label-width="110px" class="single-form">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="singleForm.name" placeholder="请输入姓名" />
            </el-form-item>
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="singleForm.phone" placeholder="请输入手机号" />
            </el-form-item>
            <el-form-item label="用户名">
              <el-input v-model="singleForm.username" placeholder="可选，不填默认使用姓名" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="singleForm.email" placeholder="可选" />
            </el-form-item>
            <el-form-item label="所属部门" prop="department_id">
              <el-select v-model="singleForm.department_id" placeholder="请选择部门（ID + 名称）" style="width: 100%">
                <el-option
                  v-for="item in departments"
                  :key="item.id"
                  :label="`${item.id} - ${item.name}`"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="用户角色" prop="role">
              <el-select v-model="singleForm.role" placeholder="请选择角色" style="width: 100%">
                <el-option label="普通用户" value="user" />
                <el-option label="审批员" value="approver" />
                <el-option label="司机" value="driver" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="singleForm.role === 'driver'" label="绑定车辆" prop="vehicle_id">
              <el-select v-model="singleForm.vehicle_id" placeholder="请选择绑定车辆" style="width: 100%">
                <el-option
                  v-for="item in vehicles"
                  :key="item.id"
                  :label="`${item.id} - ${item.plate_number}`"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item v-if="singleForm.role === 'driver'" label="驾驶证号">
              <el-input v-model="singleForm.license_number" placeholder="可选，建议填写" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loadingSingle" @click="submitSingleUser">添加用户</el-button>
              <el-button @click="resetSingleForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="批量导入" name="batch">
          <div class="batch-actions">
            <el-button type="primary" :loading="loadingBatch" @click="submitBatch">开始批量导入</el-button>
          </div>

          <el-upload
            class="upload"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            :limit="1"
            accept=".xlsx,.xls"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽或点击上传</div>
            <template #tip>
              <div class="el-upload__tip">Excel列必须包含 name、phone、department_id、department_name；role 可选 user/approver/driver；当 role=driver 时 vehicle_id 必填</div>
            </template>
          </el-upload>

          <div v-if="result" class="result mt">
            <div class="summary">
              <div>批次ID：{{ result.batch_id }}</div>
              <div>总行数：{{ result.total_rows }}</div>
              <div>成功：{{ result.success_rows }}</div>
              <div>失败：{{ result.failed_rows }}</div>
            </div>
            <el-table :data="result.failures || []" size="small" v-if="(result.failures || []).length">
              <el-table-column prop="" label="失败原因">
                <template #default="scope">{{ scope.row }}</template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, watch, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { UploadFilled } from '@element-plus/icons-vue';
import { useAuthStore } from '../stores/auth';
import { notifyError, notifySuccess } from '../utils/notify';

const router = useRouter();
const authStore = useAuthStore();
const activeTab = ref('single');
const fileList = ref([]);
const fileRef = ref(null);
const loadingSingle = ref(false);
const loadingBatch = ref(false);
const creatingDepartment = ref(false);
const savingDepartmentName = ref(false);
const replacingLeader = ref(false);
const result = ref(null);
const error = ref('');
const success = ref('');
const singleFormRef = ref(null);
const departmentFormRef = ref(null);
const departmentRenameFormRef = ref(null);
const leaderReplaceFormRef = ref(null);
const vehicles = ref([]);
const departments = ref([]);
const adminOptions = ref([]);

const singleForm = reactive({
  name: '',
  phone: '',
  username: '',
  email: '',
  department_id: null,
  role: 'user',
  vehicle_id: null,
  license_number: ''
});

const singleRules = reactive({
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  department_id: [{ required: true, message: '请选择部门', trigger: 'change' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  vehicle_id: [{
    validator: (_rule, value, callback) => {
      if (singleForm.role === 'driver' && !value) {
        callback(new Error('司机必须绑定车辆'));
        return;
      }
      callback();
    },
    trigger: 'change'
  }]
});

const departmentForm = reactive({
  name: ''
});

const departmentRules = reactive({
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }]
});

const departmentRenameForm = reactive({
  department_id: null,
  name: ''
});

const departmentRenameRules = reactive({
  department_id: [{ required: true, message: '请选择部门', trigger: 'change' }],
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }]
});

const leaderReplaceForm = reactive({
  department_id: null,
  leader_id: null
});

const leaderReplaceRules = reactive({
  department_id: [{ required: true, message: '请选择部门', trigger: 'change' }],
  leader_id: [{ required: true, message: '请选择管理员负责人', trigger: 'change' }]
});

const departmentSummary = computed(() => {
  if (!departments.value.length) return '暂无部门';
  return departments.value.map(item => `${item.id}-${item.name}${item.leader_label ? ` 负责人：${item.leader_label}` : ''}`).join('，');
});

const fetchVehicles = async () => {
  try {
    const response = await axios.get('/api/vehicles');
    vehicles.value = response.data?.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取车辆列表失败';
  }
};

const fetchDepartments = async () => {
  try {
    const response = await axios.get('/api/users/departments');
    departments.value = response.data?.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取部门列表失败';
  }
};

const fetchAdminOptions = async () => {
  try {
    const response = await axios.get('/api/users/departments/admin-options');
    adminOptions.value = response.data?.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取管理员列表失败';
  }
};

const submitDepartment = async () => {
  if (!String(departmentForm.name || '').trim()) {
    notifyError('部门名称不能为空');
    return;
  }
  try {
    await departmentFormRef.value.validate();
    creatingDepartment.value = true;
    await axios.post('/api/users/departments', {
      name: departmentForm.name
    });
    success.value = '部门创建成功，请在下方选择管理员负责人';
    departmentForm.name = '';
    await fetchDepartments();
  } catch (err) {
    error.value = err.response?.data?.message || '创建部门失败';
  } finally {
    creatingDepartment.value = false;
  }
};

const submitDepartmentRename = async () => {
  if (!departmentRenameForm.department_id) {
    notifyError('请选择需要改名的部门');
    return;
  }
  if (!String(departmentRenameForm.name || '').trim()) {
    notifyError('部门名称不能为空');
    return;
  }
  try {
    await departmentRenameFormRef.value.validate();
    savingDepartmentName.value = true;
    await axios.put(`/api/users/departments/${departmentRenameForm.department_id}`, {
      name: departmentRenameForm.name
    });
    success.value = '部门名称更新成功';
    await fetchDepartments();
  } catch (err) {
    error.value = err.response?.data?.message || '更新部门名称失败';
  } finally {
    savingDepartmentName.value = false;
  }
};

const submitReplaceLeader = async () => {
  if (!leaderReplaceForm.department_id) {
    notifyError('请选择要更换负责人的部门');
    return;
  }
  if (!leaderReplaceForm.leader_id) {
    notifyError('请选择新的负责人（管理员）');
    return;
  }
  try {
    await leaderReplaceFormRef.value.validate();
    replacingLeader.value = true;
    await axios.put(`/api/users/departments/${leaderReplaceForm.department_id}/leader`, {
      leader_id: leaderReplaceForm.leader_id
    });
    success.value = '部门负责人更换成功';
    await fetchDepartments();
  } catch (err) {
    error.value = err.response?.data?.message || '更换负责人失败';
  } finally {
    replacingLeader.value = false;
  }
};

// 选择批量导入文件并重置提示状态
const handleFileChange = (file, files) => {
  fileList.value = files.slice(-1);
  fileRef.value = file.raw;
  error.value = '';
  success.value = '';
  result.value = null;
};

// 提交单个用户导入
const submitSingleUser = async () => {
  try {
    await singleFormRef.value.validate();
    loadingSingle.value = true;
    error.value = '';
    success.value = '';

    await axios.post('/api/users', {
      name: singleForm.name,
      phone: singleForm.phone,
      username: singleForm.username || undefined,
      email: singleForm.email || undefined,
      department_id: singleForm.department_id,
      role: singleForm.role,
      vehicle_id: singleForm.role === 'driver' ? singleForm.vehicle_id : undefined,
      license_number: singleForm.role === 'driver' ? (singleForm.license_number || undefined) : undefined
    });

    success.value = '单个导入成功，默认密码为手机号';
    resetSingleForm();
  } catch (err) {
    error.value = err.response?.data?.message || '单个导入失败';
  } finally {
    loadingSingle.value = false;
  }
};

// 提交Excel批量导入
const submitBatch = async () => {
  if (!fileRef.value) {
    error.value = '请先选择Excel文件';
    return;
  }
  try {
    loadingBatch.value = true;
    error.value = '';
    success.value = '';
    const formData = new FormData();
    formData.append('file', fileRef.value);
    const res = await axios.post('/api/users/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    result.value = res.data.data;
    success.value = res.data.message || '导入完成';
  } catch (err) {
    error.value = err.response?.data?.message || '导入失败，请检查文件格式和内容';
  } finally {
    loadingBatch.value = false;
  }
};

// 重置单个导入表单与校验状态
const resetSingleForm = () => {
  singleForm.name = '';
  singleForm.phone = '';
  singleForm.username = '';
  singleForm.email = '';
  singleForm.department_id = null;
  singleForm.role = 'user';
  singleForm.vehicle_id = null;
  singleForm.license_number = '';
  singleFormRef.value?.clearValidate();
};

onMounted(() => {
  authStore.hydrate();
  if (authStore.user?.role !== 'admin') {
    notifyError('仅管理员可使用导入功能');
    router.replace('/dashboard');
    return;
  }
  fetchDepartments();
  fetchAdminOptions();
  fetchVehicles();
});

watch(error, (message) => {
  if (!message) return;
  notifyError(message);
});

watch(success, (message) => {
  if (!message) return;
  notifySuccess(message);
});

watch(() => departmentRenameForm.department_id, (departmentId) => {
  const selected = departments.value.find(item => item.id === departmentId);
  if (!selected) {
    departmentRenameForm.name = '';
    return;
  }
  departmentRenameForm.name = selected.name || '';
});

watch(() => leaderReplaceForm.department_id, (departmentId) => {
  const selected = departments.value.find(item => item.id === departmentId);
  if (!selected) {
    leaderReplaceForm.leader_id = null;
    return;
  }
  leaderReplaceForm.leader_id = selected.leader_id || null;
});
</script>

<style scoped>
.page {
  padding: 12px;
  --el-color-primary: #5f7f24;
  --el-color-primary-light-3: #88a74d;
  --el-color-primary-light-5: #a7be78;
  --el-color-primary-light-7: #c7d8a7;
  --el-color-primary-light-8: #d6e3be;
  --el-color-primary-light-9: #eaf1df;
  --el-color-primary-dark-2: #4f6c1f;
  width: 100%;
  max-width: none;
}

.batch-actions {
  margin-bottom: 12px;
}

.mt {
  margin-top: 16px;
}

.result .summary {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
  color: #2d3436;
}


:deep(.employee-dept-dropdown .el-select-dropdown__item.hover),
:deep(.employee-dept-dropdown .el-select-dropdown__item:hover) {
  background-color: rgba(95, 127, 36, 0.12) !important;
}
</style>
