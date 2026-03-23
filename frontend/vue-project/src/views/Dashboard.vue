<template>
  <el-container class="dashboard-container">
    <el-aside width="250px" class="sidebar">
      <div class="sidebar-header">
        <el-avatar :size="48" class="logo-avatar">
          <el-icon><Van /></el-icon>
        </el-avatar>
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
        <el-menu-item index="/dashboard/applications/create">
          <template #icon><el-icon><DocumentAdd /></el-icon></template>
          <span>用车申请</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/applications">
          <template #icon><el-icon><Document /></el-icon></template>
          <span>我的申请</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/approvals" v-if="isApprover || isAdmin">
          <template #icon><el-icon><Check /></el-icon></template>
          <span>审批管理</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/vehicles" v-if="isAdmin">
          <template #icon><el-icon><Van /></el-icon></template>
          <span>车辆管理</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/dispatches" v-if="isAdmin">
          <template #icon><el-icon><DataAnalysis /></el-icon></template>
          <span>调度管理</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/users/import" v-if="isApprover || isAdmin">
          <template #icon><el-icon><Upload /></el-icon></template>
          <span>批量导入</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/reports" v-if="isApprover || isAdmin">
          <template #icon><el-icon><TrendCharts /></el-icon></template>
          <span>报表可视化</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/fuel-prices" v-if="isAdmin">
          <template #icon><el-icon><Money /></el-icon></template>
          <span>油价管理</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/approver-records" v-if="isApprover || isAdmin">
          <template #icon><el-icon><Collection /></el-icon></template>
          <span>审批记录</span>
        </el-menu-item>
        <el-menu-item index="/login" @click="logout">
          <template #icon><el-icon><SwitchButton /></el-icon></template>
          <span>退出登录</span>
        </el-menu-item>
      </el-menu>
      <div class="user-info">
        <el-avatar :size="32" class="user-avatar">
          <el-icon><User /></el-icon>
        </el-avatar>
        <div class="user-details">
          <p class="username">{{ user?.username || '用户' }}</p>
          <p class="role">{{ user?.role || '角色' }}</p>
        </div>
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <div class="page-title">{{ breadcrumb }}</div>
          <div class="subtitle">{{ subtitle }}</div>
        </div>
        <div class="header-right">
          <el-tag type="success" effect="dark" class="role-tag">{{ roleLabel }}</el-tag>
          <el-button type="primary" plain size="small" @click="refreshUser">刷新信息</el-button>
          <el-dropdown v-if="isDev" trigger="click" @command="switchRole">
            <el-button size="small" plain>切换角色(开发)</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="user">普通用户</el-dropdown-item>
                <el-dropdown-item command="approver">审批员</el-dropdown-item>
                <el-dropdown-item command="admin">管理员</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content">
        <section class="hero" v-if="currentStep === 'home'">
          <div class="hero-text">
            <p class="eyebrow">欢迎回来</p>
            <h2>{{ user?.name || user?.username || '用户' }}，{{ greeting }}</h2>
            <p class="description">根据您的角色快速进入常用功能。</p>
            <div class="hero-actions">
              <el-button type="primary" @click="handleNav(primaryAction.path)">{{ primaryAction.label }}</el-button>
              <el-button plain @click="handleNav('/dashboard/applications')">查看我的申请</el-button>
            </div>
          </div>
          <div class="hero-stats">
            <el-card shadow="hover">
              <div class="stat-item">
                <p class="stat-label">角色</p>
                <p class="stat-value">{{ roleLabel }}</p>
              </div>
              <div class="stat-item">
                <p class="stat-label">今日待办</p>
                <p class="stat-value">{{ pendingCount }} 个</p>
              </div>
              <div class="stat-item">
                <p class="stat-label">上次登录</p>
                <p class="stat-value">{{ lastLoginHint }}</p>
              </div>
            </el-card>
          </div>
        </section>

        <section class="quick-actions" v-if="currentStep === 'home'">
          <div class="section-title">快速操作</div>
          <div class="action-grid">
            <el-card v-for="item in quickActions" :key="item.label" class="action-card" shadow="hover">
              <div class="action-card__content">
                <div>
                  <p class="action-label">{{ item.label }}</p>
                  <p class="action-desc">{{ item.desc }}</p>
                </div>
                <el-button type="primary" link :disabled="item.disabled" @click="handleNav(item.path)">
                  {{ item.disabled ? '规划中' : '立即前往' }}
                </el-button>
              </div>
            </el-card>
          </div>
        </section>

        <section class="info-panels" v-if="currentStep === 'home'">
          <div class="section-title">概览</div>
          <div class="panel-grid">
            <el-card class="panel-card" shadow="hover">
              <h4>审批进度</h4>
              <p class="panel-hint" v-if="isApprover">前往审批管理查看待处理事项。</p>
              <p class="panel-hint" v-else>提交申请后可在“我的申请”查看状态。</p>
            </el-card>
            <el-card class="panel-card" shadow="hover">
              <h4>车辆与费用</h4>
              <p class="panel-hint">调度完成后自动生成费用，支持按油价和油耗计算。</p>
            </el-card>
            <el-card class="panel-card" shadow="hover" v-if="isApprover || isAdmin">
              <h4>数据与可视化</h4>
              <p class="panel-hint">后端已提供报表接口，可在前端新增图表页面进行展示。</p>
            </el-card>
          </div>
        </section>

        <router-view v-else />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { DocumentAdd, Document, Check, Van, DataAnalysis, SwitchButton, Upload, TrendCharts, Money, Collection, User } from '@element-plus/icons-vue';

const router = useRouter();
const route = useRoute();
const user = ref(null);
const pendingCount = ref(0);
const lastLoginHint = computed(() => '最近登录信息暂未记录');
const currentStep = ref('home');
const isDev = import.meta.env.DEV;

const activeMenu = computed(() => {
  return route.path;
});

const role = computed(() => user.value?.role || 'user');
const isApprover = computed(() => role.value === 'leader' || role.value === 'approver');
const isAdmin = computed(() => role.value === 'admin');

const breadcrumb = computed(() => {
  const pathMap = {
    '/dashboard/applications/create': '用车申请',
    '/dashboard/applications': '我的申请',
    '/dashboard/approvals': '审批管理',
    '/dashboard/vehicles': '车辆管理',
    '/dashboard/dispatches': '调度管理',
    '/dashboard/users/import': '批量导入',
    '/dashboard/reports': '报表可视化',
    '/dashboard/fuel-prices': '油价管理',
    '/dashboard/approver-records': '审批记录'
  };
  return pathMap[route.path] || '首页';
});

const subtitle = computed(() => {
  if (isApprover.value) return '审批员工作台，查看审批与导入用户';
  if (isAdmin.value) return '管理员工作台，管理车辆与调度';
  return '快速提交用车申请，查看审批状态';
});

const roleLabel = computed(() => {
  if (isAdmin.value) return '管理员';
  if (isApprover.value) return '审批员';
  return '普通用户';
});

const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 12) return '上午好';
  if (hour < 18) return '下午好';
  return '晚上好';
});

const primaryAction = computed(() => {
  if (isApprover.value) return { label: '进入审批管理', path: '/dashboard/approvals' };
  if (isAdmin.value) return { label: '管理车辆', path: '/dashboard/vehicles' };
  return { label: '立即发起申请', path: '/dashboard/applications/create' };
});

const quickActions = computed(() => {
  const base = [
    { label: '我的申请', desc: '查看进度与审批意见', path: '/dashboard/applications' },
    { label: '创建申请', desc: '提交新的用车需求', path: '/dashboard/applications/create' }
  ];

  const approverExtra = [
    { label: '审批管理', desc: '处理待审批的用车申请', path: '/dashboard/approvals' },
    { label: '批量导入用户', desc: '支持Excel导入普通用户', path: '/dashboard/users/import' }
  ];

  const adminExtra = [
    { label: '车辆管理', desc: '维护车辆档案与状态', path: '/dashboard/vehicles' },
    { label: '调度管理', desc: '安排调度与司机', path: '/dashboard/dispatches' },
    { label: '报表可视化', desc: '查看使用率与费用趋势', path: '/dashboard/reports' },
    { label: '油价管理', desc: '维护油价并用于费用计算', path: '/dashboard/fuel-prices' },
    { label: '审批记录', desc: '查看审批员/用户的审批记录', path: '/dashboard/approver-records' }
  ];

  if (isAdmin.value) return [...approverExtra, ...adminExtra, ...base];
  if (isApprover.value) return [...approverExtra, ...base];
  return base;
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
  currentStep.value = (route.path === '/dashboard' || route.path === '/dashboard/home') ? 'home' : 'child';
});


const handleNav = (path) => {
  if (!path) return;
  router.push(path);
  if (path === '/dashboard' || path === '/dashboard/home') {
    currentStep.value = 'home';
  } else {
    currentStep.value = 'child';
  }
};

const refreshUser = () => {
  loadUser();
};

const switchRole = (roleKey) => {
  const templates = {
    user: { id: 1, username: 'user-demo', role: 'user' },
    approver: { id: 2, username: 'approver-demo', role: 'leader' },
    admin: { id: 3, username: 'admin-demo', role: 'admin' }
  };
  const payload = templates[roleKey];
  if (!payload) return;
  localStorage.setItem('user', JSON.stringify(payload));
  if (!localStorage.getItem('token')) {
    localStorage.setItem('token', 'dev-token');
  }
  loadUser();
};

watch(route, () => {
  currentStep.value = (route.path === '/dashboard' || route.path === '/dashboard/home') ? 'home' : 'child';
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

.logo-avatar {
  background: #f4f7ed;
  color: #556b2f;
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

.user-avatar {
  background: #f4f7ed;
  color: #556b2f;
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
  background: linear-gradient(120deg, #fdfaf3 0%, #f1f6e9 100%);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  padding: 18px 24px;
  border-bottom: 1px solid #e5ddd2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.page-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #2d3436;
}

.subtitle {
  color: #6b755a;
  font-size: 0.95rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.role-tag {
  border-radius: 12px;
  padding: 6px 10px;
}

.main-content {
  padding: 24px;
  overflow-y: auto;
  background-color: #f4f7ed;
  min-height: calc(100vh - 60px);
  width: 100%;
}

.hero {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.hero-text {
  background: linear-gradient(135deg, #6b8e23 0%, #556b2f 100%);
  color: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(86, 111, 46, 0.25);
}

.eyebrow {
  letter-spacing: 1px;
  text-transform: uppercase;
  opacity: 0.9;
  font-size: 0.85rem;
}

.hero-text h2 {
  margin: 10px 0;
  font-size: 1.8rem;
  font-weight: 700;
}

.description {
  margin-bottom: 16px;
  opacity: 0.92;
}

.hero-actions {
  display: flex;
  gap: 12px;
}

.hero-stats .el-card {
  height: 100%;
}

.stat-item + .stat-item {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eef1e6;
}

.stat-label {
  color: #6b755a;
  margin: 0;
  font-size: 0.95rem;
}

.stat-value {
  margin: 6px 0 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: #2d3436;
}

.quick-actions {
  margin-bottom: 24px;
}

.section-title {
  font-weight: 700;
  margin-bottom: 12px;
  color: #2d3436;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.action-card__content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.action-label {
  font-weight: 700;
  margin: 0 0 6px;
}

.action-desc {
  margin: 0;
  color: #6b755a;
  font-size: 0.95rem;
}

.info-panels {
  margin-bottom: 12px;
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.panel-card h4 {
  margin: 0 0 8px;
  font-weight: 700;
  color: #2d3436;
}

.panel-hint {
  margin: 0;
  color: #6b755a;
  line-height: 1.5;
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