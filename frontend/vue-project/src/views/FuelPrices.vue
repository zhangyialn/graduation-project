<template>
  <div class="page">
    <div class="header-row">
      <div>
        <div class="title">油价管理</div>
        <div class="hint">维护 /api/trips/fuel-prices；结束出车时费用使用最新同类型油价 * 油耗</div>
      </div>
      <div class="actions">
        <el-button plain size="small" @click="useSamplePrice">使用示例油价</el-button>
        <el-button type="primary" size="small" :loading="saving" @click="savePrice">新增油价</el-button>
      </div>
    </div>

    <el-alert v-if="error" type="error" show-icon :title="error" class="mb" />
    <el-alert v-if="success" type="success" show-icon :title="success" class="mb" />

    <el-form :model="form" label-width="120px" class="form">
      <el-form-item label="油品类型">
        <el-select v-model="form.fuel_type" placeholder="选择油品">
          <el-option label="汽油" value="汽油" />
          <el-option label="柴油" value="柴油" />
        </el-select>
      </el-form-item>
      <el-form-item label="价格 (元/升)">
        <el-input-number v-model="form.price" :min="0" :step="0.1" />
      </el-form-item>
      <el-form-item label="生效日期">
        <el-date-picker v-model="form.effective_date" type="date" value-format="YYYY-MM-DD" />
      </el-form-item>
    </el-form>

    <el-table :data="prices" size="small" class="mb">
      <el-table-column prop="fuel_type" label="油品" width="100" />
      <el-table-column prop="price" label="价格" />
      <el-table-column prop="effective_date" label="生效日期" />
      <el-table-column prop="created_at" label="创建时间" />
    </el-table>

    <el-alert type="info" show-icon class="mb" title="说明" description="结束出车时，后端会按车辆油耗和最新油价计算 fuel_cost。前端可通过此页维护最新油价，也可以替换 useSamplePrice 为真实外部油价 API 调用。" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const prices = ref([]);
const error = ref('');
const success = ref('');
const saving = ref(false);
const form = ref({
  fuel_type: '汽油',
  price: 0,
  effective_date: new Date().toISOString().slice(0, 10)
});

const token = () => localStorage.getItem('token');

const fetchPrices = async () => {
  try {
    const res = await axios.get('/api/trips/fuel-prices', {
      headers: { Authorization: `Bearer ${token()}` }
    });
    prices.value = res.data.data || [];
  } catch (err) {
    error.value = err.response?.data?.message || '获取油价失败';
  }
};

const savePrice = async () => {
  if (!form.value.price) {
    error.value = '请填写价格';
    return;
  }
  try {
    saving.value = true;
    error.value = '';
    success.value = '';
    await axios.post('/api/trips/fuel-prices', form.value, {
      headers: { Authorization: `Bearer ${token()}` }
    });
    success.value = '已保存';
    await fetchPrices();
  } catch (err) {
    error.value = err.response?.data?.message || '保存油价失败';
  } finally {
    saving.value = false;
  }
};

const useSamplePrice = () => {
  // 可替换为真实外部油价 API；此处填入示例数据避免接口限制
  form.value.price = 8.5;
  success.value = '已填入示例油价（可替换为真实API结果）';
};

onMounted(fetchPrices);
</script>

<style scoped>
.page {
  padding: 12px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
}

.title {
  font-weight: 700;
  font-size: 1.1rem;
}

.hint {
  color: #6b755a;
}

.actions {
  display: flex;
  gap: 8px;
}

.mb {
  margin-bottom: 12px;
}

.form {
  margin-bottom: 12px;
  max-width: 480px;
}
</style>
