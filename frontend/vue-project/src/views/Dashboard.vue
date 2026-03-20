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
  background-color: #343a40;
  color: white;
  display: flex;
  flex-direction: column;
  padding: 1.5rem 0;
}

.sidebar-header {
  text-align: center;
  margin-bottom: 2rem;
  padding: 0 1rem;
}

.sidebar-header h3 {
  margin: 0.5rem 0 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
}

.user-info {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-top: 1px solid #495057;
  margin-top: auto;
}

.user-details {
  margin-left: 0.75rem;
}

.username {
  margin: 0;
  font-weight: 500;
  font-size: 0.875rem;
}

.role {
  margin: 0;
  font-size: 0.75rem;
  color: #adb5bd;
}

.header {
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 0 1.5rem;
}

.main-content {
  padding: 0;
  overflow-y: auto;
  background-color: #f4f7ed;
  min-height: calc(100vh - 60px);
  width: 100%;
}
</style>