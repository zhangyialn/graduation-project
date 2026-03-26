<!-- Reports：报表可视化页面，展示趋势、费用与工作量 -->
<template>
  <div class="page">
    <div class="header-row">
      <div>
        <div class="title">报表与可视化</div>
        <div class="hint">首屏优先展示月度趋势和部门费用，其余图表收纳到“更多图表”</div>
      </div>
      <el-button type="primary" :loading="loading" @click="fetchAll">刷新数据</el-button>
    </div>

    <div class="priority-grid">
      <el-card shadow="hover">
        <template #header><div class="card-title">月度用车趋势（重点）</div></template>
        <div ref="monthlyStatsChartRef" class="chart"></div>
      </el-card>

      <el-card shadow="hover">
        <template #header><div class="card-title">部门费用统计（重点）</div></template>
        <div ref="departmentExpensesChartRef" class="chart"></div>
      </el-card>
    </div>

    <el-collapse v-model="expandedPanels" class="more-charts">
      <el-collapse-item name="more" title="更多图表">
        <div class="grid">
          <el-card shadow="hover">
            <template #header><div class="card-title">部门用车频率</div></template>
            <div ref="departmentUsageChartRef" class="chart"></div>
          </el-card>

          <el-card shadow="hover">
            <template #header><div class="card-title">车辆使用与费用</div></template>
            <div ref="vehicleUsageChartRef" class="chart"></div>
          </el-card>

          <el-card shadow="hover">
            <template #header><div class="card-title">司机工作量</div></template>
            <div ref="driverWorkloadChartRef" class="chart"></div>
          </el-card>

          <el-card shadow="hover">
            <template #header><div class="card-title">用户用车统计</div></template>
            <div ref="userStatsChartRef" class="chart"></div>
          </el-card>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue';
import axios from 'axios';
import * as echarts from 'echarts';
import { notifyError } from '../utils/notify';

const loading = ref(false);
const error = ref('');
const expandedPanels = ref([]);
const departmentUsage = ref([]);
const departmentExpenses = ref([]);
const vehicleUsage = ref([]);
const monthlyStats = ref([]);
const driverWorkload = ref([]);
const userStats = ref([]);

const departmentUsageChartRef = ref(null);
const departmentExpensesChartRef = ref(null);
const vehicleUsageChartRef = ref(null);
const monthlyStatsChartRef = ref(null);
const driverWorkloadChartRef = ref(null);
const userStatsChartRef = ref(null);

let departmentUsageChart = null;
let departmentExpensesChart = null;
let vehicleUsageChart = null;
let monthlyStatsChart = null;
let driverWorkloadChart = null;
let userStatsChart = null;

// 金额格式化为人民币文本
const currency = (value) => `¥${Number(value || 0).toFixed(2)}`;

// 并行拉取所有报表数据并触发图表渲染
const fetchAll = async () => {
  try {
    loading.value = true;
    error.value = '';
    const [deptUse, deptExp, vehicle, monthly, driver, user] = await Promise.all([
      axios.get('/api/reports/department-usage'),
      axios.get('/api/reports/department-expenses'),
      axios.get('/api/reports/vehicle-usage'),
      axios.get('/api/reports/monthly-stats'),
      axios.get('/api/reports/driver-workload'),
      axios.get('/api/reports/user-application-stats')
    ]);
    departmentUsage.value = deptUse.data.data || [];
    departmentExpenses.value = deptExp.data.data || [];
    vehicleUsage.value = vehicle.data.data || [];
    monthlyStats.value = monthly.data.data || [];
    driverWorkload.value = driver.data.data || [];
    userStats.value = user.data.data || [];
    await nextTick();
    renderAllCharts();
  } catch (err) {
    error.value = err.response?.data?.message || '获取报表数据失败';
  } finally {
    loading.value = false;
  }
};

// 获取或初始化ECharts实例
const ensureChart = (chartRef, chart) => {
  if (!chartRef.value) return chart;
  if (!chart) return echarts.init(chartRef.value);
  return chart;
};

// 渲染部门用车频率图
const renderDepartmentUsageChart = () => {
  departmentUsageChart = ensureChart(departmentUsageChartRef, departmentUsageChart);
  if (!departmentUsageChart) return;
  const labels = departmentUsage.value.map(item => item.department_label || item.department_name || '未知部门');
  const counts = departmentUsage.value.map(item => Number(item.total_count) || 0);
  departmentUsageChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 20, top: 24, bottom: 48 },
    xAxis: { type: 'category', data: labels, axisLabel: { interval: 0, rotate: labels.length > 6 ? 25 : 0 } },
    yAxis: { type: 'value', name: '次数' },
    series: [{ type: 'bar', data: counts, barWidth: '45%', itemStyle: { color: '#6b8e23' } }]
  });
};

// 渲染部门燃油费用柱状图
const renderDepartmentExpensesChart = () => {
  departmentExpensesChart = ensureChart(departmentExpensesChartRef, departmentExpensesChart);
  if (!departmentExpensesChart) return;
  const labels = departmentExpenses.value.map(item => item.department_label || item.department_name || '未知部门');
  const fuel = departmentExpenses.value.map(item => Number(item.fuel_expense) || 0);
  departmentExpensesChart.setOption({
    tooltip: { trigger: 'axis', valueFormatter: (value) => currency(value) },
    legend: { top: 0 },
    grid: { left: 56, right: 20, top: 36, bottom: 48 },
    xAxis: { type: 'category', data: labels, axisLabel: { interval: 0, rotate: labels.length > 6 ? 25 : 0 } },
    yAxis: { type: 'value', name: '费用(元)' },
    series: [
      { name: '燃油费用', type: 'bar', data: fuel, barWidth: '45%', itemStyle: { color: '#6b8e23' } }
    ]
  });
};

// 渲染车辆使用次数与费用图
const renderVehicleUsageChart = () => {
  vehicleUsageChart = ensureChart(vehicleUsageChartRef, vehicleUsageChart);
  if (!vehicleUsageChart) return;
  const labels = vehicleUsage.value.map(item => item.plate_number || `车辆${item.vehicle_id}`);
  const usage = vehicleUsage.value.map(item => Number(item.usage_count) || 0);
  const expense = vehicleUsage.value.map(item => Number(item.total_expense) || 0);
  vehicleUsageChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 56, right: 56, top: 36, bottom: 48 },
    xAxis: { type: 'category', data: labels, axisLabel: { interval: 0, rotate: labels.length > 6 ? 25 : 0 } },
    yAxis: [{ type: 'value', name: '使用次数' }, { type: 'value', name: '费用(元)' }],
    series: [
      { name: '使用次数', type: 'bar', data: usage, itemStyle: { color: '#6b8e23' } },
      { name: '总费用', type: 'line', yAxisIndex: 1, smooth: true, data: expense, itemStyle: { color: '#b47f5a' } }
    ]
  });
};

// 渲染月度申请与费用趋势图
const renderMonthlyStatsChart = () => {
  monthlyStatsChart = ensureChart(monthlyStatsChartRef, monthlyStatsChart);
  if (!monthlyStatsChart) return;
  const labels = monthlyStats.value.map(item => `${item.month}月`);
  const applications = monthlyStats.value.map(item => Number(item.application_count) || 0);
  const expenses = monthlyStats.value.map(item => Number(item.total_expense) || 0);
  monthlyStatsChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 56, right: 56, top: 36, bottom: 40 },
    xAxis: { type: 'category', data: labels },
    yAxis: [{ type: 'value', name: '申请数' }, { type: 'value', name: '费用(元)' }],
    series: [
      { name: '申请数', type: 'bar', data: applications, itemStyle: { color: '#556b2f' } },
      { name: '总费用', type: 'line', yAxisIndex: 1, smooth: true, data: expenses, itemStyle: { color: '#d4a373' } }
    ]
  });
};

// 渲染司机工作量图
const renderDriverWorkloadChart = () => {
  driverWorkloadChart = ensureChart(driverWorkloadChartRef, driverWorkloadChart);
  if (!driverWorkloadChart) return;
  const labels = driverWorkload.value.map(item => item.driver_name || '未知司机');
  const trips = driverWorkload.value.map(item => Number(item.trip_count) || 0);
  const mileage = driverWorkload.value.map(item => Number(item.total_mileage) || 0);
  driverWorkloadChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 56, right: 56, top: 36, bottom: 48 },
    xAxis: { type: 'category', data: labels, axisLabel: { interval: 0, rotate: labels.length > 6 ? 25 : 0 } },
    yAxis: [{ type: 'value', name: '行程数' }, { type: 'value', name: '里程(km)' }],
    series: [
      { name: '行程数', type: 'bar', data: trips, itemStyle: { color: '#6b8e23' } },
      { name: '里程', type: 'line', yAxisIndex: 1, smooth: true, data: mileage, itemStyle: { color: '#3d4a2b' } }
    ]
  });
};

// 渲染用户申请与费用散点图
const renderUserStatsChart = () => {
  userStatsChart = ensureChart(userStatsChartRef, userStatsChart);
  if (!userStatsChart) return;
  const points = userStats.value.map(item => ({
    name: item.user_name || `用户${item.user_id}`,
    value: [Number(item.application_count) || 0, Number(item.total_expense) || 0, Number(item.usage_count) || 0]
  }));
  userStatsChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const [applicationCount, totalExpense, usageCount] = params.value;
        return `${params.name}<br/>申请数：${applicationCount}<br/>用车次数：${usageCount}<br/>总费用：${currency(totalExpense)}`;
      }
    },
    grid: { left: 56, right: 24, top: 24, bottom: 48 },
    xAxis: { type: 'value', name: '申请数' },
    yAxis: { type: 'value', name: '总费用(元)' },
    series: [{
      type: 'scatter',
      data: points,
      symbolSize: (value) => Math.max(8, Math.min(40, (Number(value[2]) || 0) * 4 + 8)),
      itemStyle: { color: '#556b2f', opacity: 0.8 }
    }]
  });
};

// 按当前折叠面板状态渲染图表
const renderAllCharts = () => {
  renderMonthlyStatsChart();
  renderDepartmentExpensesChart();
  if (expandedPanels.value.includes('more')) {
    renderDepartmentUsageChart();
    renderVehicleUsageChart();
    renderDriverWorkloadChart();
    renderUserStatsChart();
  }
};

// 窗口尺寸变化时重绘图表尺寸
const handleResize = () => {
  departmentUsageChart?.resize();
  departmentExpensesChart?.resize();
  vehicleUsageChart?.resize();
  monthlyStatsChart?.resize();
  driverWorkloadChart?.resize();
  userStatsChart?.resize();
};

watch(expandedPanels, async () => {
  await nextTick();
  renderAllCharts();
});

watch(error, (message) => {
  if (!message) return;
  notifyError(message);
});

onMounted(async () => {
  await fetchAll();
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  departmentUsageChart?.dispose();
  departmentExpensesChart?.dispose();
  vehicleUsageChart?.dispose();
  monthlyStatsChart?.dispose();
  driverWorkloadChart?.dispose();
  userStatsChart?.dispose();
});
</script>

<style scoped>
.page { padding: 12px; }
.header-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 12px; background: #f8faf5; border: 1px solid #e3ead6; border-radius: 10px; padding: 0.9rem 1.1rem; }
.title { font-weight: 700; font-size: 1.2rem; color: #2d3436; }
.hint { color: #667459; }
.mb { margin-bottom: 12px; }
.priority-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(320px, 1fr)); gap: 12px; }
.more-charts { margin-top: 12px; }
.card-title { font-weight: 700; }
.chart { width: 100%; height: 320px; }
@media (max-width: 768px) {
  .header-row { flex-direction: column; align-items: stretch; }
  .grid { grid-template-columns: 1fr; }
  .chart { height: 260px; }
}
</style>
