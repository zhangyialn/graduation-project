<!-- 人员和车辆管理总页：聚合导入、管理员维护、车辆司机管理三块后台能力 -->
<template>
  <div class="page">
    <el-card shadow="hover" class="card">
      <template #header>
        <div class="card-header">
          <div class="title">人员和车辆管理</div>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="用户与部门" name="import">
          <UserImport v-if="activeTab === 'import'" />
        </el-tab-pane>
        <el-tab-pane label="员工维护" name="employees">
          <EmployeeManagement v-if="activeTab === 'employees'" />
        </el-tab-pane>
        <el-tab-pane label="管理员" name="admin">
          <AdminManagement v-if="activeTab === 'admin'" />
        </el-tab-pane>
        <el-tab-pane label="车辆与司机" name="vehicle-driver">
          <VehicleList v-if="activeTab === 'vehicle-driver'" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import UserImport from './UserImport.vue';
import AdminManagement from './AdminManagement.vue';
import EmployeeManagement from './EmployeeManagement.vue';
import VehicleList from '../components/Vehicle/VehicleList.vue';

// 管理后台默认先落在“人员导入”，贴合首次初始化系统的使用路径。
const activeTab = ref('import');
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
</style>
