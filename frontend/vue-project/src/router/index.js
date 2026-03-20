import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/Auth/Login.vue';
import ForgotPassword from '../components/Auth/ForgotPassword.vue';
import Dashboard from '../views/Dashboard.vue';
import CreateApplication from '../components/Application/CreateApplication.vue';
import ApplicationList from '../components/Application/ApplicationList.vue';
import ApprovalList from '../components/Approval/ApprovalList.vue';
import VehicleList from '../components/Vehicle/VehicleList.vue';
import DispatchList from '../components/Dispatch/DispatchList.vue';

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
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/applications/create',
    name: 'CreateApplication',
    component: CreateApplication
  },
  {
    path: '/applications',
    name: 'ApplicationList',
    component: ApplicationList
  },
  {
    path: '/approvals',
    name: 'ApprovalList',
    component: ApprovalList
  },
  {
    path: '/vehicles',
    name: 'VehicleList',
    component: VehicleList
  },
  {
    path: '/dispatches',
    name: 'DispatchList',
    component: DispatchList
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const token = localStorage.getItem('token');
  
  if (requiresAuth && !token) {
    next('/login');
  } else {
    next();
  }
});

export default router;