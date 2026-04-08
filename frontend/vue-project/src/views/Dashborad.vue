<!-- Dashborad：按角色展示导航、首页卡片与功能入口 -->
<template>
  <el-container class="dashboard-container">
    <el-aside v-if="showSidebar" width="270px" class="sidebar">
      <div class="sidebar-header" @click="handleNav('/dashboard/home')">
        <el-avatar :size="64" class="logo-avatar">
          <el-icon><SedanIcon /></el-icon>
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
        <el-menu-item index="/dashboard/application-center">
          <template #icon><el-icon><DocumentAdd /></el-icon></template>
          <span>申请服务中心</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/driver" v-if="isDriver">
          <template #icon><el-icon><SedanIcon /></el-icon></template>
          <span>司机面板</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/approvals" v-if="isApprover || isAdmin">
          <template #icon><el-icon><Check /></el-icon></template>
          <span>审批与出车中心</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/personnel-vehicles" v-if="isAdmin">
          <template #icon><el-icon><SedanIcon /></el-icon></template>
          <span>人员和车辆管理</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/reports" v-if="isApprover || isAdmin">
          <template #icon><el-icon><TrendCharts /></el-icon></template>
          <span>报表可视化</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/fuel-prices" v-if="isAdmin">
          <template #icon><el-icon><Money /></el-icon></template>
          <span>油价趋势分析</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header" :class="{ 'mobile-header': isMobile }">
        <div class="header-left" v-if="!isMobile && showSidebar">
          <div class="page-title">{{ breadcrumb }}</div>
        </div>

        <div class="header-left desktop-merged-nav" v-else-if="!isMobile">
          <div class="top-brand" @click="handleNav('/dashboard/home')">
            <el-avatar :size="52" class="logo-avatar top-logo-avatar">
              <el-icon><SedanIcon /></el-icon>
            </el-avatar>
            <span class="top-brand-name">公务用车系统</span>
          </div>
        </div>

        <div class="header-left mobile-left" v-else>
          <el-button text class="mobile-icon-btn" @click="handleNav('/dashboard/home')">
            <el-icon><SedanIcon /></el-icon>
          </el-button>
        </div>

        <div class="header-right" v-if="!isMobile">
          <el-dropdown trigger="click" @command="handleProfileCommand" class="profile-dropdown">
            <div class="profile-pill">
              <el-avatar :size="28" class="profile-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="profile-texts">
                <p class="profile-name">{{ user?.username || '用户' }}</p>
                <p class="profile-role">{{ roleLabel }}</p>
              </div>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="account-settings">账号设置</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-dropdown v-if="isDev" trigger="click" @command="switchRole">
            <el-button size="small" plain :loading="switchingRole">切换账号(开发)</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-if="devUsers.length === 0" disabled>暂无可切换用户</el-dropdown-item>
                <el-dropdown-item
                  v-for="item in devUsers"
                  :key="item.id"
                  :command="String(item.id)"
                >
                  {{ item.roleLabel }} · {{ item.username }}（{{ item.name || `ID:${item.id}` }}）
                </el-dropdown-item>
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
              <el-button
                v-if="primaryAction.path !== '/dashboard/application-center'"
                class="hero-sub-btn"
                @click="handleNav('/dashboard/application-center')"
              >进入申请服务中心</el-button>
            </div>
          </div>
          <div class="hero-stats">
            <el-card shadow="hover">
              <div class="stat-item">
                <p class="stat-label">角色</p>
                <p class="stat-value">{{ roleLabel }}</p>
              </div>
              <div class="stat-item stat-item-clickable" @click="goStatTarget">
                <p class="stat-label">{{ statConfig.label }}</p>
                <p class="stat-value">{{ statConfig.value }} 个</p>
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
      <el-button text class="drawer-item" @click="openAccountSettings">
        <span class="drawer-item-icon"><el-icon><Lock /></el-icon></span>
        <span class="drawer-item-text">账号设置</span>
      </el-button>
      <el-button text type="danger" class="drawer-item" @click="logout">
        <span class="drawer-item-icon"><el-icon><SwitchButton /></el-icon></span>
        <span class="drawer-item-text">退出登录</span>
      </el-button>
    </div>
  </el-drawer>

  <el-dialog
    v-model="roleLabelDialogVisible"
    title="账号设置"
    width="420px"
    class="account-settings-dialog"
    header-class="account-dialog-header"
    body-class="account-dialog-body"
    footer-class="account-dialog-footer"
    align-center
  >
    <el-form label-width="90px">
      <el-form-item label="当前角色">
        <el-input :model-value="roleLabel" disabled />
      </el-form-item>
      <el-form-item label="用户名">
        <el-input v-model="accountForm.username" placeholder="请输入用户名" maxlength="30" show-word-limit />
      </el-form-item>
      <el-form-item label="当前密码">
        <el-input v-model="accountForm.old_password" type="password" show-password placeholder="请输入当前密码" />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="accountForm.new_password" type="password" show-password placeholder="可选，留空则不修改" />
      </el-form-item>
      <el-form-item label="确认新密码">
        <el-input v-model="accountForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="roleLabelDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="savingAccount" @click="saveRoleLabelAlias">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import axios from 'axios';
import { notifyError, notifySuccess } from '../utils/notify';
import { formatBeijingDateTime, getBeijingHour } from '../utils/datetime';
import {
  DocumentAdd,
  Document,
  Check,
  DataAnalysis,
  Lock,
  SwitchButton,
  TrendCharts,
  Money,
  User,
  Menu
} from '@element-plus/icons-vue';
import SedanIcon from '../components/Common/SedanIcon.vue';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const user = ref(null);
const pendingCount = ref(0);
const rejectedCount = ref(0);
const lastLoginHint = ref('最近登录信息暂未记录');
const currentStep = ref('home');
const isDev = import.meta.env.DEV;
const screenWidth = ref(window.innerWidth);
const featureDrawer = ref(false);
const roleLabelDialogVisible = ref(false);
const savingAccount = ref(false);
const switchingRole = ref(false);
const devUsers = ref([]);
const accountForm = ref({
  username: '',
  old_password: '',
  new_password: '',
  confirm_password: ''
});

const isMobile = computed(() => screenWidth.value < 900);
const activeMenu = computed(() => route.path);
const role = computed(() => user.value?.role || 'user');
const isDriver = computed(() => role.value === 'driver');
const isApprover = computed(() => role.value === 'approver');
const isAdmin = computed(() => role.value === 'admin');
const showSidebar = computed(() => !isMobile.value && (isAdmin.value || isApprover.value));
const statConfig = computed(() => {
  if (isDriver.value) {
    return { label: '今日待办', value: pendingCount.value, path: '/dashboard/driver' };
  }
  if (isApprover.value || isAdmin.value) {
    return { label: '今日待办', value: pendingCount.value, path: '/dashboard/approval-dispatch' };
  }
  return { label: '申请未通过', value: rejectedCount.value, path: '/dashboard/applications' };
});

const breadcrumb = computed(() => {
  const pathMap = {
    '/dashboard/applications/create': '申请服务中心',
    '/dashboard/applications': '申请服务中心',
    '/dashboard/application-center': '申请服务中心',
    '/dashboard/change-password': '修改密码',
    '/dashboard/driver': '司机面板',
    '/dashboard/approval-dispatch': '审批与出车中心',
    '/dashboard/approvals': '审批与出车中心',
    '/dashboard/personnel-vehicles': '人员和车辆管理',
    '/dashboard/dispatches': '审批与出车中心',
    '/dashboard/vehicles': '人员和车辆管理',
    '/dashboard/users/import': '人员和车辆管理',
    '/dashboard/admins': '人员和车辆管理',
    '/dashboard/reports': '报表可视化',
    '/dashboard/fuel-prices': '油价趋势分析',
    '/dashboard/approver-records': '审批与出车中心',
    '/dashboard/trips': '审批与出车中心'
  };
  return pathMap[route.path] || '首页';
});

const subtitle = computed(() => {
  if (isDriver.value) return '司机工作台，查看接驾任务并填报里程油耗';
  if (isApprover.value) return '审批员工作台，专注审批与记录';
  if (isAdmin.value) return '管理员工作台，管理车辆与调度';
  return '快速提交用车申请，查看审批状态';
});

const roleLabel = computed(() => {
  if (isAdmin.value) return '管理员';
  if (isApprover.value) return '审批员';
  if (isDriver.value) return '司机';
  return '普通用户';
});

const greeting = computed(() => {
  const hour = getBeijingHour();
  if (hour < 12) return '上午好';
  if (hour < 18) return '下午好';
  return '晚上好';
});

const primaryAction = computed(() => {
  if (isDriver.value) return { label: '进入司机面板', path: '/dashboard/driver' };
  if (isApprover.value) return { label: '进入审批与出车中心', path: '/dashboard/approval-dispatch' };
  if (isAdmin.value) return { label: '人员和车辆管理', path: '/dashboard/personnel-vehicles' };
  return { label: '进入申请服务中心', path: '/dashboard/application-center' };
});

const quickActions = computed(() => {
  const base = [
    { label: '申请服务中心', desc: '发起申请并查看进度', path: '/dashboard/application-center' }
  ];

  const approverExtra = [
    { label: '审批与出车中心', desc: '处理审批、调度、记录和行程', path: '/dashboard/approval-dispatch' }
  ];

  const driverExtra = [
    { label: '司机面板', desc: '查看接驾任务并填报里程油耗', path: '/dashboard/driver' }
  ];

  const adminExtra = [
    { label: '人员和车辆管理', desc: '导入人员、管理员维护与车辆司机管理', path: '/dashboard/personnel-vehicles' },
    { label: '审批与出车中心', desc: '处理审批、调度、记录和行程', path: '/dashboard/approval-dispatch' },
    { label: '报表可视化', desc: '查看使用率与费用趋势', path: '/dashboard/reports' },
    { label: '油价趋势分析', desc: '查看油价曲线并用于费用计算', path: '/dashboard/fuel-prices' }
  ];

  if (isAdmin.value) return [...adminExtra, ...base];
  if (isDriver.value) return [...driverExtra, ...base];
  if (isApprover.value) return [...approverExtra, ...base];
  return base;
});

const featureTips = computed(() => {
  const approvalText = isApprover.value
    ? '前往审批与出车中心查看待处理事项。'
    : '提交申请后可在“申请服务中心”查看状态。';
  const reportText = isApprover.value || isAdmin.value
    ? '后端已提供报表接口，可在报表可视化中查看趋势。'
    : '如需查看可视化趋势，请联系审批员或管理员。';

  return [
    { title: '司机任务', text: isDriver.value ? '在司机面板查看出发时间、起点和乘客电话。' : '调度完成后司机可在司机面板处理行程。' },
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
        { label: '申请服务中心', path: '/dashboard/application-center', icon: DocumentAdd }
      ]
    }
  ];

  if (isApprover.value || isAdmin.value) {
    groups.push({
      title: '审批',
      items: [
        { label: '审批与出车中心', path: '/dashboard/approval-dispatch', icon: Check },
        { label: '报表可视化', path: '/dashboard/reports', icon: TrendCharts }
      ]
    });
  }

  if (isDriver.value) {
    groups.push({
      title: '司机',
      items: [
        { label: '司机面板', path: '/dashboard/driver', icon: SedanIcon }
      ]
    });
  }

  if (isAdmin.value) {
    groups.push({
      title: '用户与资源',
      items: [
        { label: '人员和车辆管理', path: '/dashboard/personnel-vehicles', icon: User }
      ]
    });

    groups.push({
      title: '调度与车辆',
      items: [
        { label: '审批与出车中心', path: '/dashboard/approval-dispatch', icon: DataAnalysis },
        { label: '油价趋势分析', path: '/dashboard/fuel-prices', icon: Money }
      ]
    });
  }

  return groups;
});

const roleLabelMap = {
  admin: '管理员',
  approver: '审批员',
  driver: '司机',
  user: '普通用户'
};

const resolveRoleLabel = (roleKey) => roleLabelMap[roleKey] || roleKey || '未知角色';

// 从本地会话恢复当前用户信息
const loadUser = () => {
  authStore.hydrate();
  user.value = authStore.user || null;
};

const loadLastLoginHint = () => {
  try {
    const username = user.value?.username;
    if (!username) {
      lastLoginHint.value = '最近登录信息暂未记录';
      return;
    }
    const lastKey = `login-last-meta:${username}`;
    const currentKey = `login-current-meta:${username}`;
    const raw = localStorage.getItem(lastKey) || localStorage.getItem(currentKey);
    if (!raw) {
      lastLoginHint.value = '最近登录信息暂未记录';
      return;
    }
    const parsed = JSON.parse(raw);
    const timeText = formatBeijingDateTime(parsed?.time);
    const locationText = parsed?.location || '未知地点';
    lastLoginHint.value = `${timeText} · ${locationText}`;
  } catch (_err) {
    lastLoginHint.value = '最近登录信息暂未记录';
  }
};

const fetchRolePendingCount = async () => {
  try {
    if (!user.value) {
      pendingCount.value = 0;
      rejectedCount.value = 0;
      return;
    }

    if (isDriver.value) {
      const response = await axios.get('/api/drivers/me/dashboard');
      const tasks = response.data?.data?.tasks || [];
      pendingCount.value = tasks.filter((item) => ['scheduled', 'in_progress'].includes(item.dispatch_status)).length;
      return;
    }

    if (isApprover.value) {
      const departmentId = user.value?.department_id;
      if (!departmentId) {
        pendingCount.value = 0;
        return;
      }
      const response = await axios.get(`/api/applications/pending/${departmentId}`);
      pendingCount.value = (response.data?.data || []).length;
      return;
    }

    if (isAdmin.value) {
      const response = await axios.get('/api/applications', { params: { status: 'pending' } });
      pendingCount.value = (response.data?.data || []).length;
      return;
    }

    const response = await axios.get(`/api/applications/my/${user.value.id}`);
    const list = response.data?.data || [];
    rejectedCount.value = list.filter((item) => item.status === 'rejected').length;
  } catch (_err) {
    pendingCount.value = 0;
    rejectedCount.value = 0;
  }
};

const goStatTarget = () => {
  if (!statConfig.value?.path) return;
  handleNav(statConfig.value.path);
};

// 清理登录态并跳转登录页
const logout = () => {
  authStore.clearSession();
  handleNav('/login');
};

// 统一处理导航与首页/子页状态切换
const handleNav = (path) => {
  featureDrawer.value = false;
  if (!path) return;
  router.push(path);
  currentStep.value = (path === '/dashboard' || path === '/dashboard/home') ? 'home' : 'child';
};

// 手动刷新用户资料
const refreshUser = () => loadUser();

const handleProfileCommand = (command) => {
  if (command === 'account-settings') {
    openAccountSettings();
    return;
  }
  if (command === 'logout') {
    logout();
  }
};

const openAccountSettings = () => {
  accountForm.value = {
    username: user.value?.username || '',
    old_password: '',
    new_password: '',
    confirm_password: ''
  };
  roleLabelDialogVisible.value = true;
  featureDrawer.value = false;
};

const saveRoleLabelAlias = async () => {
  const username = (accountForm.value.username || '').trim();
  const oldPassword = (accountForm.value.old_password || '').trim();
  const newPassword = (accountForm.value.new_password || '').trim();
  const confirmPassword = (accountForm.value.confirm_password || '').trim();

  if (!username) {
    notifyError('用户名不能为空');
    return;
  }
  if (!oldPassword) {
    notifyError('请输入当前密码');
    return;
  }
  if (newPassword && newPassword.length < 6) {
    notifyError('新密码至少6位');
    return;
  }
  if (newPassword && newPassword !== confirmPassword) {
    notifyError('两次输入的新密码不一致');
    return;
  }

  try {
    savingAccount.value = true;
    const res = await axios.post('/api/auth/account-settings', {
      username,
      old_password: oldPassword,
      new_password: newPassword || undefined
    });
    const latestUser = res.data?.data;
    if (latestUser) {
      authStore.setUser(latestUser);
      user.value = latestUser;
    }
    notifySuccess('账号设置已更新');
    roleLabelDialogVisible.value = false;
  } catch (err) {
    notifyError(err.response?.data?.message || '账号设置更新失败');
  } finally {
    savingAccount.value = false;
  }
};

const fetchDevUsers = async () => {
  if (!isDev || !authStore.token) return;
  try {
    const response = await axios.get('/api/auth/dev-users');
    const list = response.data?.data || [];
    devUsers.value = list.map((item) => ({
      ...item,
      roleLabel: resolveRoleLabel(item.role)
    }));
  } catch (_err) {
    devUsers.value = [];
  }
};

// 开发环境下切换为数据库中的任意用户（返回真实JWT）
const switchRole = async (userIdText) => {
  if (!isDev) return;
  const targetUserId = Number(userIdText);
  if (!Number.isFinite(targetUserId) || targetUserId <= 0) return;

  try {
    switchingRole.value = true;
    const response = await axios.post('/api/auth/dev-switch-user', { user_id: targetUserId });
    const payload = response.data?.data;
    if (!payload?.access_token || !payload?.user) {
      notifyError('角色切换失败：响应数据不完整');
      return;
    }

    // 开发模式固定使用 session，保证不同标签页互不干扰
    authStore.setSession(payload.access_token, payload.user, 'session');
    loadUser();
    await fetchDevUsers();
    await fetchRolePendingCount();
    loadLastLoginHint();

    const targetPath = payload.user?.must_change_password ? '/dashboard/change-password' : '/dashboard/home';
    handleNav(targetPath);
    notifySuccess(`已切换为：${payload.user.username}（${resolveRoleLabel(payload.user.role)}）`);
  } catch (err) {
    notifyError(err.response?.data?.message || '切换角色失败');
  } finally {
    switchingRole.value = false;
  }
};

// 更新屏幕宽度用于移动端判断
const updateWidth = () => {
  screenWidth.value = window.innerWidth;
};

onMounted(() => {
  loadUser();
  loadLastLoginHint();
  fetchRolePendingCount();
  fetchDevUsers();
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

watch(() => user.value?.username, () => {
  loadLastLoginHint();
  fetchRolePendingCount();
});
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
  padding: 1.5rem 0 1rem;
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
  background: transparent;
  color: #eef3e1;
}

.logo-avatar :deep(.el-icon) {
  font-size: 30px;
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

.desktop-merged-nav {
  flex-direction: row;
  align-items: center;
  gap: 10px;
}

.top-brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.top-logo-avatar {
  color: #2f4727;
}

.top-brand-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: #2d3436;
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

.profile-dropdown {
  cursor: pointer;
}

.profile-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px 4px 6px;
  border: 1px solid #d8e1c7;
  border-radius: 999px;
  background: #ffffff;
}

.profile-avatar {
  background: #eef3df;
  color: #556b2f;
}

.profile-texts {
  display: flex;
  flex-direction: column;
}

.profile-name {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.2;
  color: #2d3436;
}

.profile-role {
  margin: 0;
  font-size: 11px;
  line-height: 1.2;
  color: #6b755a;
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

.stat-item-clickable {
  cursor: pointer;
}

.stat-item-clickable:hover .stat-value {
  color: #3f581d;
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

:deep(.tips-card .el-card__body) {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 16px;
  row-gap: 6px;
  align-items: start;
}

.tip-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 0;
}

.tip-row + .tip-row {
  border-top: none;
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
  margin: 2px 0 0;
  color: #6b755a;
  line-height: 1.35;
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

:deep(.drawer-content .el-button + .el-button) {
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

:global(.account-settings-dialog) {
  border-radius: 12px;
}

:global(.account-dialog-header) {
  padding: 22px 24px 20px;
  text-align: center;
}

:global(.account-dialog-header .el-dialog__title) {
  font-size: 26px;
  font-weight: 700;
  line-height: 1.2;
  color: #2d3436;
  display: inline-block;
}

:global(.account-dialog-body) {
  padding: 26px 24px 10px;
}

:global(.account-dialog-body .el-form) {
  padding-top: 8px;
}

:global(.account-dialog-body .el-form-item) {
  margin-bottom: 18px;
}

:global(.account-dialog-body .el-form-item__label) {
  font-size: 15px;
  font-weight: 700;
  color: #2d3436;
}

:global(.account-dialog-body .el-input__wrapper) {
  padding: 8px 12px;
}

:global(.account-dialog-body .el-input__inner) {
  font-size: 18px;
  font-weight: 500;
}

:global(.account-dialog-footer) {
  padding: 14px 22px 22px;
}

:global(.account-dialog-footer .el-button) {
  min-width: 96px;
  font-size: 16px;
  font-weight: 600;
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

  .tips-card {
    display: block;
  }

  :deep(.tips-card .el-card__body) {
    grid-template-columns: 1fr;
  }

  .action-card__content {
    display: block;
  }
}
</style>
