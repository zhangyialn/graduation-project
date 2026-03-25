<template>
  <el-card class="detail-card" shadow="hover">
    <template #header>
      <div class="header">
        <el-button text @click="router.back()">返回</el-button>
        <span>审批详情</span>
      </div>
    </template>

    <el-skeleton :loading="loading" animated>
      <template #template>
        <el-skeleton-item variant="text" style="width: 60%; margin-bottom: 10px" />
        <el-skeleton-item variant="rect" style="height: 180px" />
      </template>

      <div class="info" v-if="application">
        <p><b>申请ID：</b>{{ application.id }}</p>
        <p><b>申请人ID：</b>{{ application.applicant_id }}</p>
        <p><b>部门ID：</b>{{ application.department_id }}</p>
        <p><b>用车事由：</b>{{ application.purpose }}</p>
        <p><b>起点：</b>{{ application.start_point || '-' }}</p>
        <p><b>目的地：</b>{{ application.destination }}</p>
        <p><b>人数：</b>{{ application.passenger_count }}</p>
        <p><b>出发时间：</b>{{ formatDate(application.start_time) }}</p>
        <p><b>当前状态：</b><el-tag :type="statusType(application.status)">{{ application.status }}</el-tag></p>
      </div>

      <el-divider>审批操作</el-divider>
      <el-form :model="form" label-position="top">
        <el-form-item label="审批设置起点（可覆盖申请人填写）">
          <el-input v-model="form.start_point" placeholder="请输入起点" />
        </el-form-item>
        <el-form-item label="审批意见">
          <el-input v-model="form.comment" type="textarea" :rows="4" maxlength="200" show-word-limit placeholder="请输入审批意见" />
        </el-form-item>
        <div class="actions">
          <el-button type="success" :loading="submitting" @click="submit('approved')">同意</el-button>
          <el-button type="danger" :loading="submitting" @click="submit('rejected')">驳回</el-button>
        </div>
      </el-form>

      <el-divider>历史审批</el-divider>
      <div v-if="approvals.length === 0" class="empty">暂无审批记录</div>
      <div v-else class="history">
        <el-card v-for="item in approvals" :key="item.id" shadow="never" class="history-item">
          <p><b>审批人：</b>{{ item.approver_id }}</p>
          <p><b>结果：</b><el-tag :type="statusType(item.status)">{{ item.status }}</el-tag></p>
          <p><b>意见：</b>{{ item.comment || '-' }}</p>
          <p><b>时间：</b>{{ formatDate(item.approved_at) }}</p>
        </el-card>
      </div>
    </el-skeleton>

  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { notifyError, notifySuccess } from '../../utils/notify';

const route = useRoute();
const router = useRouter();
const application = ref(null);
const approvals = ref([]);
const loading = ref(false);
const submitting = ref(false);
const error = ref('');
const form = reactive({ comment: '', start_point: '' });

const statusType = (status) => ({ pending: 'warning', approved: 'success', rejected: 'danger', completed: 'info' }[status] || 'info');
const formatDate = (v) => v ? new Date(v).toLocaleString() : '-';

const fetchData = async () => {
  try {
    loading.value = true;
    error.value = '';
    const id = route.params.applicationId;
    const [appRes, approvalRes] = await Promise.all([
      axios.get(`/api/applications/${id}`),
      axios.get(`/api/approvals/application/${id}`)
    ]);
    application.value = appRes.data.data;
    form.start_point = application.value?.start_point || '';
    approvals.value = approvalRes.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取审批详情失败';
  } finally {
    loading.value = false;
  }
};

const submit = async (status) => {
  try {
    if (!application.value) return;
    submitting.value = true;
    error.value = '';
    await axios.post(`/api/approvals/application/${application.value.id}/submit`, {
      status,
      comment: form.comment,
      start_point: form.start_point
    });
    notifySuccess(status === 'approved' ? '审批已同意' : '审批已驳回');
    await fetchData();
  } catch (err) {
    error.value = err.response?.data?.message || '提交审批失败';
  } finally {
    submitting.value = false;
  }
};

onMounted(fetchData);

watch(error, (message) => {
  if (!message) return;
  notifyError(message);
});
</script>

<style scoped>
.detail-card { max-width: 900px; margin: 0 auto; }
.header { display: flex; align-items: center; gap: 8px; font-weight: 700; }
.info p { margin: 0 0 8px; }
.actions { display: flex; gap: 10px; }
.empty { color: #7a8770; }
.history { display: grid; gap: 10px; }
.history-item p { margin: 0 0 6px; }
.mt { margin-top: 12px; }
@media (max-width: 768px) {
  .actions { flex-direction: column; }
  .actions .el-button { width: 100%; }
}
</style>
