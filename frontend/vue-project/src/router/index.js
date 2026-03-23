import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/Auth/Login.vue';
import ForgotPassword from '../components/Auth/ForgotPassword.vue';
import Dashboard from '../views/Dashborad.vue';
import CreateApplication from '../components/Application/CreateApplication.vue';
import ApplicationList from '../components/Application/ApplicationList.vue';
import ApprovalList from '../components/Approval/ApprovalLiat.vue';
import ApprovalDetail from '../components/Approval/ApprovalDetail.vue';
import VehicleList from '../components/Vehicle/VehicleList.vue';
import DispatchList from '../components/Dispatch/DispatchList.vue';
import UserImport from '../views/UserImport.vue';
import Reports from '../views/Reports.vue';
import FuelPrices from '../views/FuelPrices.vue';
import ApproverRecords from '../views/ApproverRecords.vue';

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
      { path: 'users/import', name: 'UserImport', component: UserImport, meta: { requiresAuth: true } },
      { path: 'reports', name: 'Reports', component: Reports, meta: { requiresAuth: true } },
      { path: 'fuel-prices', name: 'FuelPrices', component: FuelPrices, meta: { requiresAuth: true } },
      { path: 'approver-records', name: 'ApproverRecords', component: ApproverRecords, meta: { requiresAuth: true } }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 路由守卫
router.beforeEach((to) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const token = localStorage.getItem('token');
  if (!requiresAuth) return true;
  // 开发环境放行，便于无登录预览
  if (import.meta.env.DEV) return true;
  if (requiresAuth && !token) {
    return '/login';
  }
  return true;
});

export default router;