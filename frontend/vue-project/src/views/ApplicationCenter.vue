<!-- 申请服务中心：把“发起申请/我的申请”合并为页签，减少用户在子路由间来回跳转 -->
<template>
  <el-card class="merged-card" shadow="hover">
    <template #header>
      <div class="header">申请服务中心</div>
    </template>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="发起申请" name="create">
        <CreateApplication v-if="activeTab === 'create'" />
      </el-tab-pane>
      <el-tab-pane label="我的申请" name="list">
        <ApplicationList v-if="activeTab === 'list'" />
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import CreateApplication from '../components/Application/CreateApplication.vue';
import ApplicationList from '../components/Application/ApplicationList.vue';

const route = useRoute();
const router = useRouter();

// 地址栏路径映射到页签，保证刷新后仍停在对应功能。
const getTabByPath = (path) => {
  if (path.includes('/applications/create')) return 'create';
  if (path.includes('/applications')) return 'list';
  return 'create';
};

// 页签映射到路由路径，用于地址栏同步。
const getPathByTab = (tab) => (tab === 'list' ? '/dashboard/applications' : '/dashboard/applications/create');

const activeTab = ref(getTabByPath(route.path));

watch(activeTab, (tab) => {
  // 切换页签时同步 URL，便于浏览器前进后退与链接分享。
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
