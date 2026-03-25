<!-- UserImport：管理员导入普通用户与审批员（单个/批量） -->
<template>
  <div class="page">
    <el-card shadow="hover" class="card">
      <template #header>
        <div class="card-header">
          <div>
            <div class="title">用户导入功能</div>
            <div class="hint">支持单个导入与Excel批量导入，仅支持普通用户与审批员</div>
          </div>
        </div>
      </template>

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
              <el-input v-model="singleForm.username" placeholder="可选，不填自动生成" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="singleForm.email" placeholder="可选" />
            </el-form-item>
            <el-form-item label="部门ID">
              <el-input-number v-model="singleForm.department_id" :min="1" controls-position="right" />
            </el-form-item>
            <el-form-item label="用户角色" prop="role">
              <el-select v-model="singleForm.role" placeholder="请选择角色" style="width: 100%">
                <el-option label="普通用户" value="user" />
                <el-option label="审批员" value="approver" />
              </el-select>
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
              <div class="el-upload__tip">Excel列至少包含 name、phone，可选 role(仅 user/approver)</div>
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
import { reactive, ref, watch, onMounted } from 'vue';
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
const result = ref(null);
const error = ref('');
const success = ref('');
const singleFormRef = ref(null);

const singleForm = reactive({
  name: '',
  phone: '',
  username: '',
  email: '',
  department_id: null,
  role: 'user'
});

const singleRules = reactive({
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
});

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
      department_id: singleForm.department_id || undefined,
      role: singleForm.role
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
  singleFormRef.value?.clearValidate();
};

onMounted(() => {
  authStore.hydrate();
  if (authStore.user?.role !== 'admin') {
    notifyError('仅管理员可使用导入功能');
    router.replace('/dashboard');
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
</script>

<style scoped>
.page {
  padding: 12px;
}

.card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #f8faf5;
  border: 1px solid #e3ead6;
  border-radius: 10px;
  padding: 0.9rem 1.1rem;
}

.title {
  font-weight: 700;
  font-size: 1.2rem;
  color: #2d3436;
}

.hint {
  color: #667459;
  font-size: 0.95rem;
}

.upload {
  width: 100%;
}

.single-form {
  max-width: 680px;
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
</style>
