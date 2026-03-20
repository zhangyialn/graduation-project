<template>
  <el-container class="dashboard-container">
    <el-aside width="250px" class="sidebar">
      <div class="sidebar-header">
        <el-avatar :size="48" src="https://img.icons8.com/color/96/000000/car.png" />
        <h3>公务用车系统</h3>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        background-color="#343a40"
        text-color="#fff"
        active-text-color="#409EFF"
        router
      >
        <el-menu-item index="/applications/create">
          <template #icon><el-icon><DocumentAdd /></el-icon></template>
          <span>用车申请</span>
        </el-menu-item>
        <el-menu-item index="/applications">
          <template #icon><el-icon><Document /></el-icon></template>
          <span>我的申请</span>
        </el-menu-item>
        <el-menu-item index="/approvals" v-if="user?.role === 'leader'">
          <template #icon><el-icon><Check /></el-icon></template>
          <span>审批管理</span>
        </el-menu-item>
        <el-menu-item index="/vehicles" v-if="user?.role === 'admin'">
          <template #icon><el-icon><Van /></el-icon></template>
          <span>车辆管理</span>
        </el-menu-item>
        <el-menu-item index="/dispatches" v-if="user?.role === 'admin'">
          <template #icon><el-icon><DataAnalysis /></el-icon></template>
          <span>调度管理</span>
        </el-menu-item>
        <el-menu-item index="/login" @click="logout">
          <template #icon><el-icon><SwitchButton /></el-icon></template>
          <span>退出登录</span>
        </el-menu-item>
      </el-menu>
      <div class="user-info">
        <el-avatar :size="32" :src="userAvatar" />
        <div class="user-details">
          <p class="username">{{ user?.username || '用户' }}</p>
          <p class="role">{{ user?.role || '角色' }}</p>
        </div>
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>{{ breadcrumb }}</el-breadcrumb-item>
        </el-breadcrumb>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { DocumentAdd, Document, Check, Van, DataAnalysis, SwitchButton } from '@element-plus/icons-vue';

const router = useRouter();
const route = useRoute();
const user = ref(null);
const userAvatar = ref('https://img.icons8.com/color/96/000000/user.png');

const activeMenu = computed(() => {
  return route.path;
});

const breadcrumb = computed(() => {
  const pathMap = {
    '/applications/create': '用车申请',
    '/applications': '我的申请',
    '/approvals': '审批管理',
    '/vehicles': '车辆管理',
    '/dispatches': '调度管理'
  };
  return pathMap[route.path] || '首页';
});

const loadUser = () => {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    user.value = JSON.parse(userStr);
  }
};

const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  router.push('/login');
};

onMounted(() => {
  loadUser();
});

watch(route, () => {
  // 路由变化时的处理
}, { deep: true });
</script>

<style scoped>
.dashboard-container {
  height: 100vh;
  background-color: #f4f7ed;
}

.sidebar {
  background: linear-gradient(180deg, #3d4a2b 0%, #4a5a35 100%);
  color: white;
  display: flex;
  flex-direction: column;
  padding: 1.5rem 0;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.sidebar-header {
  text-align: center;
  margin-bottom: 2rem;
  padding: 0 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 1.5rem;
}

.sidebar-header h3 {
  margin: 0.5rem 0 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: #ecf0f1;
  letter-spacing: 0.5px;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
}

:deep(.sidebar-menu) {
  flex: 1;
  border-right: none;
  background-color: transparent !important;
}

:deep(.sidebar-menu .el-menu-item) {
  background-color: transparent !important;
  transition: all 0.3s ease;
  margin: 4px 8px;
  border-radius: 6px;
  color: #ecf0f1;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.sidebar-menu .el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.1) !important;
  transform: translateX(4px);
}

:deep(.sidebar-menu .is-active) {
  background: linear-gradient(135deg, #6b8e23 0%, #556b2f 100%) !important;
  border-radius: 6px;
}

.user-info {
  display: flex;
  align-items: center;
  padding: 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: auto;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  margin: 1rem 0.75rem 0 0.75rem;
}

.user-details {
  margin-left: 0.75rem;
}

.username {
  margin: 0;
  font-weight: 600;
  font-size: 0.875rem;
  color: #ecf0f1;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
}

.role {
  margin: 0;
  font-size: 0.75rem;
  color: #bdc3c7;
}

.header {
  background: linear-gradient(90deg, #ffffff 0%, #fefdfb 100%);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  padding: 0 1.5rem;
  border-bottom: 1px solid #e5ddd2;
}

:deep(.el-breadcrumb__item) {
  color: #2d3436;
}

:deep(.el-breadcrumb__separator) {
  color: #d4c5b9;
}

.main-content {
  padding: 24px;
  overflow-y: auto;
  background-color: #f4f7ed;
  min-height: calc(100vh - 60px);
  width: 100%;
}

.main-content::-webkit-scrollbar {
  width: 8px;
}

.main-content::-webkit-scrollbar-track {
  background: transparent;
}

.main-content::-webkit-scrollbar-thumb {
  background: #d4c5b9;
  border-radius: 4px;
  transition: background 0.3s ease;
}

.main-content::-webkit-scrollbar-thumb:hover {
  background: #6b8e23;
}
</style>