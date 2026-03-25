/**
 * 路由配置：定义登录/初始化/仪表盘子路由，并通过全局守卫做登录态与角色控制。
 */
import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/Auth/Login.vue';
import ForgotPassword from '../components/Auth/ForgotPassword.vue';
import BootstrapAdmin from '../components/Auth/BootstrapAdmin.vue';
import ChangePassword from '../components/Auth/ChangePassword.vue';
import Dashboard from '../views/Dashborad.vue';
import CreateApplication from '../components/Application/CreateApplication.vue';
import ApplicationList from '../components/Application/ApplicationList.vue';
import ApprovalList from '../components/Approval/ApprovalLiat.vue';
import ApprovalDetail from '../components/Approval/ApprovalDetail.vue';
import VehicleList from '../components/Vehicle/VehicleList.vue';
import DispatchList from '../components/Dispatch/DispatchList.vue';
import UserImport from '../views/UserImport.vue';
import AdminManagement from '../views/AdminManagement.vue';
import Reports from '../views/Reports.vue';
import FuelPrices from '../views/FuelPrices.vue';
import ApproverRecords from '../views/ApproverRecords.vue';
import DriverDashboard from '../components/Driver/DriverDashboard.vue';
import { useAuthStore } from '../stores/auth';
import { pinia } from '../stores/pinia';

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: ForgotPassword
  },
  {
    path: '/bootstrap-admin',
    name: 'BootstrapAdmin',
    component: BootstrapAdmin
  },

  {
    path: '/dashboard',
    component: Dashboard,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: { name: 'DashboardHome' } },
      { path: 'home', name: 'DashboardHome', component: { template: '<div />' }, meta: { requiresAuth: true } },
      { path: 'applications/create', name: 'CreateApplication', component: CreateApplication, meta: { requiresAuth: true } },
      { path: 'applications', name: 'ApplicationList', component: ApplicationList, meta: { requiresAuth: true } },
      { path: 'approvals', name: 'ApprovalList', component: ApprovalList, meta: { requiresAuth: true } },
      { path: 'approvals/:applicationId', name: 'ApprovalDetail', component: ApprovalDetail, meta: { requiresAuth: true } },
      { path: 'vehicles', name: 'VehicleList', component: VehicleList, meta: { requiresAuth: true } },
      { path: 'dispatches', name: 'DispatchList', component: DispatchList, meta: { requiresAuth: true } },
      { path: 'users/import', name: 'UserImport', component: UserImport, meta: { requiresAuth: true, roles: ['admin'] } },
      { path: 'admins', name: 'AdminManagement', component: AdminManagement, meta: { requiresAuth: true, roles: ['admin'] } },
      { path: 'reports', name: 'Reports', component: Reports, meta: { requiresAuth: true } },
      { path: 'fuel-prices', name: 'FuelPrices', component: FuelPrices, meta: { requiresAuth: true } },
      { path: 'approver-records', name: 'ApproverRecords', component: ApproverRecords, meta: { requiresAuth: true } },
      { path: 'driver', name: 'DriverDashboard', component: DriverDashboard, meta: { requiresAuth: true } },
      { path: 'change-password', name: 'ChangePassword', component: ChangePassword, meta: { requiresAuth: true } }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 全局前置守卫：处理未登录拦截、强制改密、以及按路由元信息做角色鉴权
router.beforeEach((to) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const allowedRoles = to.matched.find(record => Array.isArray(record.meta?.roles))?.meta?.roles;
  const authStore = useAuthStore(pinia);
  authStore.hydrate();
  const token = authStore.token;
  const mustChangePassword = !!authStore.user?.must_change_password;
  const role = authStore.user?.role;
  const isChangePasswordRoute = to.path === '/dashboard/change-password';
  if (!requiresAuth) return true;
  if (requiresAuth && !token) {
    return '/login';
  }
  if (mustChangePassword && !isChangePasswordRoute) {
    return '/dashboard/change-password';
  }
  if (allowedRoles && (!role || !allowedRoles.includes(role))) {
    return '/dashboard';
  }
  return true;
});

export default router;
