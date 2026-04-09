<!-- ApproverRecords：审批员查看个人与全量审批记录 -->
<template>
  <div class="page">
    <div class="header-row">
      <div>
        <div class="title">审批记录</div>
        <div class="hint">审批员查看自己的记录或全部记录；按状态筛选</div>
      </div>
      <div class="filters">
        <el-select v-model="status" placeholder="按状态筛选" clearable>
          <el-option label="全部" value="" />
          <el-option label="通过" value="approved" />
          <el-option label="驳回" value="rejected" />
          <el-option label="待审批" value="pending" />
        </el-select>
        <el-button type="primary" :loading="loading" @click="fetchData">刷新</el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="我的审批" name="mine">
        <div v-if="isMobile" class="mobile-list">
          <el-card v-for="item in myApprovals" :key="item.id" shadow="never" class="mobile-item">
            <p class="mobile-title">审批 #{{ item.id }}</p>
            <p class="mobile-line">申请ID：{{ item.application_id ?? '-' }}</p>
            <p class="mobile-line">状态：{{ item.status || '-' }}</p>
            <p class="mobile-line">意见：{{ item.comment || '-' }}</p>
            <p class="mobile-line">时间：{{ formatDate(item.approved_at || item.created_at) }}</p>
          </el-card>
        </div>
        <el-table v-else :data="myApprovals" size="small">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="application_id" label="申请ID" width="90" />
          <el-table-column prop="status" label="状态" />
          <el-table-column prop="comment" label="意见" />
          <el-table-column label="时间">
            <template #default="scope">{{ formatDate(scope.row.approved_at || scope.row.created_at) }}</template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="myTotal > pageSize"
          class="pager"
          background
          layout="prev, pager, next, total"
          :current-page="myPage"
          :page-size="pageSize"
          :total="myTotal"
          @current-change="onMyPageChange"
        />
      </el-tab-pane>
      <el-tab-pane label="全部审批" name="all">
        <div v-if="isMobile" class="mobile-list">
          <el-card v-for="item in allApprovals" :key="item.id" shadow="never" class="mobile-item">
            <p class="mobile-title">审批 #{{ item.id }}</p>
            <p class="mobile-line">申请ID：{{ item.application_id ?? '-' }}</p>
            <p class="mobile-line">审批人：{{ item.approver_id ?? '-' }}</p>
            <p class="mobile-line">状态：{{ item.status || '-' }}</p>
            <p class="mobile-line">意见：{{ item.comment || '-' }}</p>
            <p class="mobile-line">时间：{{ formatDate(item.approved_at || item.created_at) }}</p>
          </el-card>
        </div>
        <el-table v-else :data="allApprovals" size="small">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="application_id" label="申请ID" width="90" />
          <el-table-column prop="approver_id" label="审批人" width="90" />
          <el-table-column prop="status" label="状态" />
          <el-table-column prop="comment" label="意见" />
          <el-table-column label="时间">
            <template #default="scope">{{ formatDate(scope.row.approved_at || scope.row.created_at) }}</template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="allTotal > pageSize"
          class="pager"
          background
          layout="prev, pager, next, total"
          :current-page="allPage"
          :page-size="pageSize"
          :total="allTotal"
          @current-change="onAllPageChange"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import { notifyError } from '../utils/notify';
import { formatBeijingDateTime } from '../utils/datetime';

const myApprovals = ref([]);
const allApprovals = ref([]);
const status = ref('');
const loading = ref(false);
const error = ref('');
const activeTab = ref('mine');
// “我的审批”和“全部审批”独立页码，切页签时保留各自阅读位置。
const pageSize = ref(10);
const myPage = ref(1);
const allPage = ref(1);
const myTotal = ref(0);
const allTotal = ref(0);
const screenWidth = ref(window.innerWidth);
const isMobile = computed(() => screenWidth.value < 900);
const authStore = useAuthStore();
// 审批时间统一转为北京时间文本。
const formatDate = (value) => formatBeijingDateTime(value);

// 根据当前筛选条件加载审批记录数据
const fetchData = async () => {
  try {
    loading.value = true;
    error.value = '';
    const user = authStore.user;
    const [mineRes, allRes] = await Promise.all([
      user ? axios.get(`/api/approvals/approver/${user.id}`, {
        params: {
          page: myPage.value,
          limit: pageSize.value
        }
      }) : Promise.resolve({ data: { data: [], pagination: { total: 0 } } }),
      axios.get('/api/approvals', {
        params: {
          status: status.value || undefined,
          page: allPage.value,
          limit: pageSize.value
        }
      })
    ]);
    myApprovals.value = mineRes.data.data || [];
    allApprovals.value = allRes.data.data || [];
    // 兼容后端未返回 pagination 的情况，至少保证分页组件渲染正确。
    myTotal.value = mineRes.data?.pagination?.total || myApprovals.value.length;
    allTotal.value = allRes.data?.pagination?.total || allApprovals.value.length;
  } catch (err) {
    error.value = err.response?.data?.message || '获取审批记录失败';
  } finally {
    loading.value = false;
  }
};

// “我的审批”分页回调。
const onMyPageChange = async (nextPage) => {
  myPage.value = nextPage;
  await fetchData();
};

// “全部审批”分页回调。
const onAllPageChange = async (nextPage) => {
  allPage.value = nextPage;
  await fetchData();
};

// 更新屏幕宽度用于移动端适配
const updateWidth = () => {
  screenWidth.value = window.innerWidth;
};

onMounted(() => {
  fetchData();
  window.addEventListener('resize', updateWidth);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateWidth);
});

watch(error, (message) => {
  if (!message) return;
  notifyError(message);
});

watch(status, async () => {
  // 切换状态筛选后回到第一页，避免筛选后落在空页。
  myPage.value = 1;
  allPage.value = 1;
  await fetchData();
});
</script>

<style scoped>
.page {
  padding: 12px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
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
}

.filters {
  display: flex;
  gap: 8px;
}

.mb {
  margin-bottom: 12px;
}

.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.mobile-list {
  display: grid;
  gap: 10px;
}

.mobile-item {
  border-radius: 10px;
}

.mobile-title {
  margin: 0;
  font-weight: 700;
  color: #2d3436;
}

.mobile-line {
  margin: 8px 0 0;
  color: #4d5b44;
  font-size: 13px;
}

@media (max-width: 899px) {
  .header-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filters {
    width: 100%;
    flex-direction: column;
  }
}
</style>
