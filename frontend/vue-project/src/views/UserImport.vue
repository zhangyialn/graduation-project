<template>
  <div class="page">
    <el-card shadow="hover" class="card">
      <template #header>
        <div class="card-header">
          <div>
            <div class="title">用户批量导入（Excel）</div>
          </div>
          <el-button type="primary" :loading="loading" @click="submit">开始导入</el-button>
        </div>
      </template>

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
          <div class="el-upload__tip">文件仅保留在浏览器内存，提交时携带到服务器</div>
        </template>
      </el-upload>

      <el-alert v-if="error" type="error" show-icon :title="error" class="mt" />
      <el-alert v-if="success" type="success" show-icon :title="success" class="mt" />

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
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { UploadFilled } from '@element-plus/icons-vue';

const fileList = ref([]);
const fileRef = ref(null);
const loading = ref(false);
const result = ref(null);
const error = ref('');
const success = ref('');

const handleFileChange = (file, files) => {
  fileList.value = files.slice(-1);
  fileRef.value = file.raw;
  error.value = '';
  success.value = '';
  result.value = null;
};

const submit = async () => {
  if (!fileRef.value) {
    error.value = '请先选择Excel文件';
    return;
  }
  try {
    loading.value = true;
    error.value = '';
    success.value = '';
    const formData = new FormData();
    formData.append('file', fileRef.value);
    const token = localStorage.getItem('token');
    const res = await axios.post('/api/users/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${token}`
      }
    });
    result.value = res.data.data;
    success.value = res.data.message || '导入完成';
  } catch (err) {
    error.value = err.response?.data?.message || '导入失败，请检查文件格式和内容';
  } finally {
    loading.value = false;
  }
};
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
