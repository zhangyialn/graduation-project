/**
 * 路由配置：定义登录/初始化/仪表盘子路由，并通过全局守卫做登录态与角色控制。
 */
import { createRouter, createWebHashHistory } from 'vue-router';
import Login from '../components/Auth/Login.vue';
import ForgotPassword from '../components/Auth/ForgotPassword.vue';
import BootstrapAdmin from '../components/Auth/BootstrapAdmin.vue';
import ChangePassword from '../components/Auth/ChangePassword.vue';
import Dashboard from '../views/Dashborad.vue';
import ApplicationCenter from '../views/ApplicationCenter.vue';
import ApprovalDispatchManagement from '../views/ApprovalDispatchManagement.vue';
import ApprovalDetail from '../components/Approval/ApprovalDetail.vue';
import PersonnelVehicleManagement from '../views/PersonnelVehicleManagement.vue';
import Reports from '../views/Reports.vue';
import FuelPrices from '../views/FuelPrices.vue';
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
      { path: 'applications/create', name: 'CreateApplication', component: ApplicationCenter, meta: { requiresAuth: true } },
      { path: 'applications', name: 'ApplicationList', component: ApplicationCenter, meta: { requiresAuth: true } },
      { path: 'application-center', name: 'ApplicationCenter', component: ApplicationCenter, meta: { requiresAuth: true } },
      { path: 'approval-dispatch', name: 'ApprovalDispatchManagement', component: ApprovalDispatchManagement, meta: { requiresAuth: true, roles: ['approver', 'admin'] } },
      { path: 'approvals', name: 'ApprovalList', component: ApprovalDispatchManagement, meta: { requiresAuth: true, roles: ['approver', 'admin'] } },
      { path: 'approvals/:applicationId', name: 'ApprovalDetail', component: ApprovalDetail, meta: { requiresAuth: true } },
      { path: 'vehicles', name: 'VehicleList', component: PersonnelVehicleManagement, meta: { requiresAuth: true, roles: ['admin'] } },
      { path: 'dispatches', name: 'DispatchList', component: ApprovalDispatchManagement, meta: { requiresAuth: true, roles: ['approver', 'admin'] } },
      { path: 'personnel-vehicles', name: 'PersonnelVehicleManagement', component: PersonnelVehicleManagement, meta: { requiresAuth: true, roles: ['admin'] } },
      { path: 'users/import', name: 'UserImport', component: PersonnelVehicleManagement, meta: { requiresAuth: true, roles: ['admin'] } },
      { path: 'admins', name: 'AdminManagement', component: PersonnelVehicleManagement, meta: { requiresAuth: true, roles: ['admin'] } },
      { path: 'reports', name: 'Reports', component: Reports, meta: { requiresAuth: true } },
      { path: 'fuel-prices', name: 'FuelPrices', component: FuelPrices, meta: { requiresAuth: true } },
      { path: 'approver-records', name: 'ApproverRecords', component: ApprovalDispatchManagement, meta: { requiresAuth: true, roles: ['approver', 'admin'] } },
      { path: 'trips', name: 'TripManagement', component: ApprovalDispatchManagement, meta: { requiresAuth: true, roles: ['approver', 'admin'] } },
      { path: 'driver', name: 'DriverDashboard', component: DriverDashboard, meta: { requiresAuth: true } },
      { path: 'change-password', name: 'ChangePassword', component: ChangePassword, meta: { requiresAuth: true } }
    ]
  }
];

const history = createWebHashHistory();

const router = createRouter({
  history,
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
