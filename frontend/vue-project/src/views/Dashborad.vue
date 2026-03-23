<template>
  <el-container class="dashboard-container">
    <el-aside v-if="!isMobile" width="250px" class="sidebar">
      <div class="sidebar-header" @click="handleNav('/dashboard/home')">
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
      <el-header class="header" :class="{ 'mobile-header': isMobile }">
        <div class="header-left" v-if="!isMobile">
          <div class="page-title">{{ breadcrumb }}</div>
        </div>

        <div class="header-left mobile-left" v-else>
          <el-button text class="mobile-icon-btn" @click="handleNav('/dashboard/home')">
            <el-icon><Van /></el-icon>
          </el-button>
        </div>

        <div class="header-right" v-if="!isMobile">
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

        <div class="header-right" v-else>
          <el-button text class="mobile-icon-btn" @click="featureDrawer = true">
            <el-icon><Menu /></el-icon>
          </el-button>
        </div>
      </el-header>

      <el-main class="main-content">
        <section class="hero" v-if="currentStep === 'home'">
          <div class="hero-text">
            <p class="eyebrow">欢迎回来</p>
            <h2>{{ user?.name || user?.username || '用户' }}，{{ greeting }}</h2>
            <p class="description">根据您的角色快速进入常用功能。</p>
            <div class="hero-actions">
              <el-button class="hero-main-btn" @click="handleNav(primaryAction.path)">{{ primaryAction.label }}</el-button>
              <el-button class="hero-sub-btn" @click="handleNav('/dashboard/applications')">查看我的申请</el-button>
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
            <el-card
              v-for="item in quickActions"
              :key="item.label"
              class="action-card"
              shadow="hover"
              @click="handleNav(item.path)"
            >
              <div class="action-card__content">
                <div>
                  <p class="action-label">{{ item.label }}</p>
                  <p class="action-desc">{{ item.desc }}</p>
                </div>
              </div>
            </el-card>
          </div>
        </section>

        <section class="info-panels" v-if="currentStep === 'home'">
          <div class="section-title">功能提示</div>
          <el-card class="tips-card" shadow="never">
            <div class="tip-row" v-for="tip in featureTips" :key="tip.title">
              <span class="tip-dot" />
              <div>
                <p class="tip-title">{{ tip.title }}</p>
                <p class="tip-text">{{ tip.text }}</p>
              </div>
            </div>
          </el-card>
        </section>

        <router-view v-else />
      </el-main>
    </el-container>
  </el-container>

  <el-drawer v-model="featureDrawer" direction="ltr" size="82%" :with-header="false" v-if="isMobile">
    <div class="drawer-content">
      <p class="drawer-title">功能菜单</p>
      <div v-for="group in menuGroups" :key="group.title" class="drawer-group">
        <p class="drawer-group-title">{{ group.title }}</p>
        <el-button v-for="item in group.items" :key="item.path" text class="drawer-item" @click="handleNav(item.path)">
          <span class="drawer-item-icon"><el-icon><component :is="item.icon" /></el-icon></span>
          <span class="drawer-item-text">{{ item.label }}</span>
        </el-button>
      </div>

      <el-divider />
      <div class="user-panel">
        <el-avatar :size="40"><el-icon><User /></el-icon></el-avatar>
        <div>
          <p class="user-name">{{ user?.username || '用户' }}</p>
          <p class="user-role">当前身份：{{ roleLabel }}</p>
        </div>
      </div>
      <el-button text type="danger" class="drawer-item" @click="logout">
        <span class="drawer-item-icon"><el-icon><SwitchButton /></el-icon></span>
        <span class="drawer-item-text">退出登录</span>
      </el-button>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import {
  DocumentAdd,
  Document,
  Check,
  Van,
  DataAnalysis,
  SwitchButton,
  Upload,
  TrendCharts,
  Money,
  Collection,
  User,
  Menu
} from '@element-plus/icons-vue';

const router = useRouter();
const route = useRoute();
const user = ref(null);
const pendingCount = ref(0);
const lastLoginHint = computed(() => '最近登录信息暂未记录');
const currentStep = ref('home');
const isDev = import.meta.env.DEV;
const screenWidth = ref(window.innerWidth);
const featureDrawer = ref(false);

const isMobile = computed(() => screenWidth.value < 900);
const activeMenu = computed(() => route.path);
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

const featureTips = computed(() => {
  const approvalText = isApprover.value
    ? '前往审批管理查看待处理事项。'
    : '提交申请后可在“我的申请”查看状态。';
  const reportText = isApprover.value || isAdmin.value
    ? '后端已提供报表接口，可在报表可视化中查看趋势。'
    : '如需查看可视化趋势，请联系审批员或管理员。';

  return [
    { title: '审批进度', text: approvalText },
    { title: '车辆与费用', text: '调度完成后自动生成费用，支持按油价和油耗计算。' },
    { title: '数据与可视化', text: reportText }
  ];
});

const menuGroups = computed(() => {
  const groups = [
    {
      title: '申请',
      items: [
        { label: '用车申请', path: '/dashboard/applications/create', icon: DocumentAdd },
        { label: '我的申请', path: '/dashboard/applications', icon: Document }
      ]
    }
  ];

  if (isApprover.value || isAdmin.value) {
    groups.push({
      title: '审批',
      items: [
        { label: '审批管理', path: '/dashboard/approvals', icon: Check },
        { label: '批量导入', path: '/dashboard/users/import', icon: Upload },
        { label: '报表可视化', path: '/dashboard/reports', icon: TrendCharts },
        { label: '审批记录', path: '/dashboard/approver-records', icon: Collection }
      ]
    });
  }

  if (isAdmin.value) {
    groups.push({
      title: '调度与车辆',
      items: [
        { label: '车辆管理', path: '/dashboard/vehicles', icon: Van },
        { label: '调度管理', path: '/dashboard/dispatches', icon: DataAnalysis },
        { label: '油价管理', path: '/dashboard/fuel-prices', icon: Money }
      ]
    });
  }

  return groups;
});

const loadUser = () => {
  const userStr = localStorage.getItem('user');
  if (userStr) user.value = JSON.parse(userStr);
};

const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  handleNav('/login');
};

const handleNav = (path) => {
  featureDrawer.value = false;
  if (!path) return;
  router.push(path);
  currentStep.value = (path === '/dashboard' || path === '/dashboard/home') ? 'home' : 'child';
};

const refreshUser = () => loadUser();

const switchRole = (roleKey) => {
  const templates = {
    user: { id: 1, username: 'user-demo', role: 'user' },
    approver: { id: 2, username: 'approver-demo', role: 'leader' },
    admin: { id: 3, username: 'admin-demo', role: 'admin' }
  };
  const payload = templates[roleKey];
  if (!payload) return;
  localStorage.setItem('user', JSON.stringify(payload));
  if (!localStorage.getItem('token')) localStorage.setItem('token', 'dev-token');
  loadUser();
};

const updateWidth = () => {
  screenWidth.value = window.innerWidth;
};

onMounted(() => {
  loadUser();
  currentStep.value = (route.path === '/dashboard' || route.path === '/dashboard/home') ? 'home' : 'child';
  window.addEventListener('resize', updateWidth);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateWidth);
});

watch(route, () => {
  currentStep.value = (route.path === '/dashboard' || route.path === '/dashboard/home') ? 'home' : 'child';
  featureDrawer.value = false;
}, { deep: true });
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background-color: #f4f7ed;
}

.sidebar {
  background: #425430;
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
  cursor: pointer;
}

.sidebar-header h3 {
  margin: 0.5rem 0 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: #ecf0f1;
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
}

:deep(.sidebar-menu .el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.1) !important;
  transform: translateX(4px);
}

:deep(.sidebar-menu .is-active) {
  background: #5f7f24 !important;
}

.user-info {
  display: flex;
  align-items: center;
  padding: 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: auto;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  margin: 1rem 0.75rem 0;
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
}

.role {
  margin: 0;
  font-size: 0.75rem;
  color: #bdc3c7;
}

.header {
  background: #f1f4ea;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  padding: 18px 24px;
  border-bottom: 1px solid #e5ddd2;
  position: sticky;
  top: 0;
  z-index: 1000;
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
  background: #5f7f24;
  color: #fff;
  padding: 24px;
  border-radius: 12px;
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

.hero-main-btn {
  background: #4d6a24;
  border-color: #4d6a24;
  color: #ffffff;
  transition: all 0.2s ease;
}

.hero-main-btn:hover,
.hero-main-btn:focus {
  background: #3f581d;
  border-color: #3f581d;
  color: #ffffff;
}

.hero-sub-btn {
  background: #edf3e1;
  border-color: #d5e1bf;
  color: #3f581d;
  transition: all 0.2s ease;
}

.hero-sub-btn:hover,
.hero-sub-btn:focus {
  background: #e3ecd1;
  border-color: #c6d7a8;
  color: #2f4727;
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
  display: block;
}

.action-card {
  cursor: pointer;
}

.action-entry {
  margin: 8px 0 0;
  color: #556b2f;
  font-size: 0.9rem;
  font-weight: 600;
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

.tips-card {
  border: 1px solid #dfe6d2;
  background: #fbfcf8;
}

.tip-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 0;
}

.tip-row + .tip-row {
  border-top: 1px dashed #d9dfcc;
}

.tip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6b8e23;
  margin-top: 7px;
}

.tip-title {
  margin: 0;
  font-weight: 700;
  color: #2d3436;
}

.tip-text {
  margin: 3px 0 0;
  color: #6b755a;
  line-height: 1.5;
}

.drawer-content {
  padding: 12px;
}

.drawer-title {
  margin: 0 0 10px;
  font-weight: 700;
  font-size: 18px;
}

.drawer-group {
  margin-bottom: 14px;
}

.drawer-group-title {
  margin: 0 0 6px;
  font-size: 12px;
  color: #667459;
}

.drawer-item {
  width: 100%;
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin-bottom: 6px;
  padding: 2px 0 !important;
}

:deep(.drawer-group .el-button + .el-button) {
  margin-left: 0 !important;
}

:deep(.drawer-item > span) {
  width: 100%;
  display: grid;
  grid-template-columns: 26px 1fr;
  align-items: center;
  column-gap: 10px;
}

.drawer-item-icon {
  width: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.drawer-item-icon :deep(.el-icon) {
  font-size: 18px;
}

.drawer-item-text {
  text-align: left;
  font-size: 16px;
  line-height: 1.3;
}

.user-panel {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
}

.user-name {
  margin: 0;
  font-weight: 700;
}

.user-role {
  margin: 2px 0 0;
  font-size: 13px;
  color: #5f6b54;
}

.mobile-icon-btn {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #ffffff !important;
  width: 44px;
  height: 44px;
  padding: 0 !important;
}

.mobile-icon-btn :deep(.el-icon) {
  font-size: 28px;
}

.mobile-icon-btn:hover {
  background: transparent !important;
}

@media (max-width: 899px) {
  .mobile-header {
    background: #2f4727;
    border-bottom: none;
    box-shadow: none;
    padding: max(10px, env(safe-area-inset-top)) 12px 10px;
    border-radius: 0;
    display: flex;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: space-between;
    gap: 0;
  }

  .mobile-header .header-left,
  .mobile-header .header-right {
    width: auto !important;
    flex: 0 0 auto;
  }

  .mobile-header .header-right {
    margin-left: auto;
    justify-content: flex-end !important;
  }

  .mobile-header .page-title,
  .mobile-header .subtitle {
    color: #ffffff;
  }

  .mobile-left {
    flex-direction: row;
    align-items: center;
    gap: 10px;
  }

  .main-content {
    padding: 12px;
  }

  .hero {
    grid-template-columns: 1fr;
  }

  .hero-text {
    padding: 16px;
  }

  .hero-text h2 {
    font-size: 1.4rem;
  }

  .action-grid,
  .panel-grid {
    grid-template-columns: 1fr;
  }

  .action-card__content {
    display: block;
  }
}
</style>
