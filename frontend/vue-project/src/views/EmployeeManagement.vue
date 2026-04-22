<template>
  <div class="page">
    <el-card shadow="hover" class="card">
      <template #header>
        <div class="card-header">
          <div class="title">员工维护</div>
          <div class="hint">支持刷新员工列表、更改所属部门、删除离职员工</div>
        </div>
      </template>

      <div class="toolbar">
        <el-button type="primary" plain :loading="loadingUsers" @click="fetchUsers">刷新员工列表</el-button>
      </div>

      <div v-if="isMobile" class="mobile-list" v-loading="loadingUsers">
        <el-card v-for="item in employeeUsers" :key="item.id" shadow="never" class="mobile-item">
          <p class="mobile-line"><b>员工ID：</b>{{ item.id }}</p>
          <p class="mobile-line"><b>姓名：</b>{{ item.name || '-' }}</p>
          <p class="mobile-line"><b>手机号：</b>{{ item.phone || '-' }}</p>
          <p class="mobile-line"><b>角色：</b>{{ roleLabel(item.role) }}</p>
          <p class="mobile-line"><b>当前部门：</b>{{ departmentNameById(item.department_id) }}</p>
          <el-select v-model="item.next_department_id" placeholder="选择新部门" class="mobile-select" popper-class="employee-dept-dropdown">
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="`${dept.id} - ${dept.name}`"
              :value="dept.id"
            />
          </el-select>
          <div class="mobile-actions">
            <el-button link class="change-dept-btn" :loading="updatingUserId === item.id" @click="updateUserDepartment(item)">更改部门</el-button>
            <el-button type="danger" link :loading="deletingUserId === item.id" @click="deleteEmployee(item)">删除员工</el-button>
          </div>
        </el-card>
      </div>

      <el-table v-else :data="employeeUsers" border size="small" v-loading="loadingUsers">
        <el-table-column prop="id" label="员工ID" width="90" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="scope">{{ roleLabel(scope.row.role) }}</template>
        </el-table-column>
        <el-table-column label="当前部门" min-width="180">
          <template #default="scope">{{ departmentNameById(scope.row.department_id) }}</template>
        </el-table-column>
        <el-table-column label="调整部门" min-width="220">
          <template #default="scope">
            <el-select v-model="scope.row.next_department_id" placeholder="选择新部门" style="width: 200px" popper-class="employee-dept-dropdown">
              <el-option
                v-for="item in departments"
                :key="item.id"
                :label="`${item.id} - ${item.name}`"
                :value="item.id"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button link class="change-dept-btn" :loading="updatingUserId === scope.row.id" @click="updateUserDepartment(scope.row)">更改部门</el-button>
            <el-button type="danger" link :loading="deletingUserId === scope.row.id" @click="deleteEmployee(scope.row)">删除员工</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-dialog
        v-model="deleteDialogVisible"
        title="删除确认"
        width="420px"
        align-center
        class="employee-delete-dialog"
      >
        <p class="delete-dialog-text">
          确认删除员工“{{ pendingDeleteUser?.name }}（{{ pendingDeleteUser?.id }}）”吗？此操作将执行软删除。
        </p>
        <template #footer>
          <div class="delete-dialog-footer">
            <el-button @click="deleteDialogVisible = false">取消</el-button>
            <el-button
              type="danger"
              :loading="deletingUserId === pendingDeleteUser?.id"
              @click="confirmDeleteEmployee"
            >确认删除</el-button>
          </div>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import { notifyError, notifySuccess } from '../utils/notify';

const router = useRouter();
const authStore = useAuthStore();
const loadingUsers = ref(false);
const updatingUserId = ref(null);
const deletingUserId = ref(null);
const employeeUsers = ref([]);
const departments = ref([]);
const error = ref('');
const success = ref('');
const deleteDialogVisible = ref(false);
const pendingDeleteUser = ref(null);
const screenWidth = ref(window.innerWidth);
const isMobile = computed(() => screenWidth.value < 900);

const roleLabel = (role) => ({
  user: '普通用户',
  approver: '审批员',
  driver: '司机',
  admin: '管理员'
}[role] || role || '-');

const departmentNameById = (departmentId) => {
  const department = departments.value.find(item => item.id === departmentId);
  return department ? `${department.id} - ${department.name}` : '-';
};

const fetchDepartments = async () => {
  try {
    const response = await axios.get('/api/users/departments');
    departments.value = response.data?.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取部门列表失败';
  }
};

const fetchUsers = async () => {
  try {
    loadingUsers.value = true;
    const response = await axios.get('/api/users');
    const users = response.data?.data || [];
    employeeUsers.value = users
      .filter(item => item.role !== 'admin')
      .map(item => ({
        ...item,
        next_department_id: item.department_id
      }));
  } catch (err) {
    error.value = err.response?.data?.message || '获取员工列表失败';
  } finally {
    loadingUsers.value = false;
  }
};

const updateUserDepartment = async (userRow) => {
  if (!userRow?.id) return;
  if (!userRow.next_department_id) {
    notifyError('请选择新的部门');
    return;
  }
  if (userRow.next_department_id === userRow.department_id) {
    notifySuccess('部门未变化，无需更新');
    return;
  }
  try {
    updatingUserId.value = userRow.id;
    await axios.put(`/api/users/${userRow.id}`, {
      department_id: userRow.next_department_id
    });
    success.value = `已更新 ${userRow.name} 的所属部门`;
    await fetchUsers();
  } catch (err) {
    error.value = err.response?.data?.message || '更改员工部门失败';
  } finally {
    updatingUserId.value = null;
  }
};

const deleteEmployee = async (userRow) => {
  if (!userRow?.id) return;
  pendingDeleteUser.value = userRow;
  deleteDialogVisible.value = true;
};

const confirmDeleteEmployee = async () => {
  const userRow = pendingDeleteUser.value;
  if (!userRow?.id) return;
  try {
    deletingUserId.value = userRow.id;
    await axios.delete(`/api/users/${userRow.id}`);
    success.value = `已删除员工 ${userRow.name}`;
    deleteDialogVisible.value = false;
    pendingDeleteUser.value = null;
    await fetchUsers();
  } catch (err) {
    error.value = err.response?.data?.message || '删除员工失败';
  } finally {
    deletingUserId.value = null;
  }
};

const updateWidth = () => {
  screenWidth.value = window.innerWidth;
};

onMounted(async () => {
  authStore.hydrate();
  if (authStore.user?.role !== 'admin') {
    notifyError('仅管理员可访问员工维护');
    router.replace('/dashboard');
    return;
  }
  await fetchDepartments();
  await fetchUsers();
  window.addEventListener('resize', updateWidth);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateWidth);
});

watch(error, (message) => {
  if (!message) return;
  notifyError(message);
});

watch(success, (message) => {
  if (!message) return;
  notifySuccess(message);
});
</script>

<style scoped>
.page {
  padding: 12px;
}

.card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #2d3436;
}

.hint {
  color: #667459;
  font-size: 0.95rem;
}

.toolbar {
  margin-bottom: 12px;
}

.mobile-list {
  display: grid;
  gap: 10px;
}

.mobile-item {
  border-radius: 10px;
}

.mobile-line {
  margin: 0 0 8px;
}

.mobile-select {
  width: 100%;
}

.mobile-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.delete-dialog-text {
  color: #2f3a31;
  line-height: 1.7;
}

.delete-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.change-dept-btn.el-button) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #5f7f24 !important;
  padding-left: 0;
  padding-right: 0;
}

:global(.employee-dept-dropdown .el-select-dropdown__item.is-selected),
:global(.employee-dept-dropdown .el-select-dropdown__item.selected) {
  color: #5f7f24 !important;
  font-weight: 700;
}

:global(.employee-dept-dropdown .el-select-dropdown__item.hover),
:global(.employee-dept-dropdown .el-select-dropdown__item:hover) {
  background-color: rgba(95, 127, 36, 0.12) !important;
}
</style>
