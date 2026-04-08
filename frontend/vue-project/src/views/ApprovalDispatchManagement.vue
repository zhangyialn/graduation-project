<template>
  <el-card class="merged-card" shadow="hover">
    <template #header>
      <div class="header">审批与出车中心</div>
    </template>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="未审批管理" name="approval">
        <ApprovalList v-if="activeTab === 'approval'" />
      </el-tab-pane>
      <el-tab-pane label="调度管理" name="dispatch">
        <DispatchList v-if="activeTab === 'dispatch'" />
      </el-tab-pane>
      <el-tab-pane label="审批记录" name="records">
        <ApproverRecords v-if="activeTab === 'records'" />
      </el-tab-pane>
      <el-tab-pane label="行程管理" name="trips">
        <TripManagement v-if="activeTab === 'trips'" />
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ApprovalList from '../components/Approval/ApprovalLiat.vue';
import DispatchList from '../components/Dispatch/DispatchList.vue';
import ApproverRecords from './ApproverRecords.vue';
import TripManagement from '../components/Trip/TripManagement.vue';

const route = useRoute();
const router = useRouter();
const getTabByPath = (path) => {
  if (path.includes('/dispatches')) return 'dispatch';
  if (path.includes('/approver-records')) return 'records';
  if (path.includes('/trips')) return 'trips';
  return 'approval';
};

const getPathByTab = (tab) => {
  if (tab === 'dispatch') return '/dashboard/dispatches';
  if (tab === 'records') return '/dashboard/approver-records';
  if (tab === 'trips') return '/dashboard/trips';
  return '/dashboard/approvals';
};

const activeTab = ref(getTabByPath(route.path));

watch(activeTab, (tab) => {
  const target = getPathByTab(tab);
  if (route.path !== target) {
    router.replace(target);
  }
});

watch(() => route.path, (path) => {
  activeTab.value = getTabByPath(path);
});
</script>

<style scoped>
.merged-card { max-width: 1240px; margin: 0 auto; }
.header { font-size: 16px; font-weight: 700; color: #2d3436; }
</style>
