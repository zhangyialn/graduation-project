<!-- FuelPrices：按地区获取并展示当日油价 -->
<template>
  <div class="page">
    <div class="header-row">
      <div>
        <div class="title">油价趋势分析</div>
        <div class="hint">按地区获取当日油价并回填展示；结束出车时费用使用最新同类型油价 * 油耗</div>
        <div class="hint" v-if="cacheHint">{{ cacheHint }}</div>
        <div class="hint" v-if="locationHint">{{ locationHint }}</div>
      </div>
    </div>

    <el-form :model="form" label-width="120px" class="form">
      <el-form-item label="地区">
        <el-select v-model="form.region_name" filterable placeholder="请选择地区" @change="onRegionChange">
          <el-option v-for="item in provinceOptions" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
      <el-form-item label="油品型号">
        <el-select v-model="form.fuel_type" placeholder="选择油品">
          <el-option label="92号汽油" value="92号汽油" />
          <el-option label="95号汽油" value="95号汽油" />
          <el-option label="98号汽油" value="98号汽油" />
          <el-option label="0号柴油" value="0号柴油" />
        </el-select>
      </el-form-item>
      <el-form-item label="价格 (元/升)">
        <el-input-number v-model="form.price" :min="0" :step="0.1" :disabled="true" />
      </el-form-item>
      <el-form-item label="生效日期">
        <el-date-picker v-model="form.effective_date" type="date" value-format="YYYY-MM-DD" :disabled="true" />
      </el-form-item>
      <el-form-item label="截至日期">
        <el-date-picker
          v-model="form.selected_date"
          type="date"
          placeholder="请选择日期"
          value-format="YYYY-MM-DD"
          :disabled-date="disabledFutureDate"
        />
        <div class="range-hint">基于所选日期向前最多展示15次油价更新</div>
      </el-form-item>
    </el-form>

    <div class="chart-block mb">
      <div class="chart-title">油价历史折线图（最多15次）</div>
      <div v-if="!chartData.dates.length" class="chart-empty">当前筛选范围暂无可视化数据</div>
      <div v-else ref="chartRef" class="chart" />
    </div>

    <div class="info-note mb">
      <div class="info-note-title">说明</div>
      <div class="info-note-text">结束出车时，后端会按车辆油耗和最新油价计算 fuel_cost。油价接口每天仅请求一次，结果保存在 Pinia（并持久化到本地），本页不支持手动新增油价。</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, onBeforeUnmount, nextTick } from 'vue';
import axios from 'axios';
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { TooltipComponent, LegendComponent, GridComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { useFuelPriceStore } from '../stores/fuelPrice';
import { notifyError, notifySuccess } from '../utils/notify';
import { formatBeijingDateTime, getBeijingDateKey } from '../utils/datetime';

// 仅注册本页实际使用的图表与组件，降低 ECharts 打包体积。
echarts.use([LineChart, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer]);

const prices = ref([]);
const error = ref('');
const success = ref('');
const fuelStore = useFuelPriceStore();
const chartRef = ref(null);
let chartInstance = null;
const MAX_POINTS = 15;
const provinceSuffixRegexp = /(省|市|自治区|特别行政区|壮族自治区|回族自治区|维吾尔自治区)$/;

const normalizeProvinceName = (value) => String(value || '').trim().replace(provinceSuffixRegexp, '');
// 生成当天日期（YYYY-MM-DD）
const today = () => getBeijingDateKey();
// 油价时间统一格式化为北京时间展示。
const formatDate = (value) => formatBeijingDateTime(value);

// 禁止选择未来日期，避免出现无效查询范围。
const disabledFutureDate = (date) => {
  const endOfToday = new Date();
  endOfToday.setHours(23, 59, 59, 999);
  return date.getTime() > endOfToday.getTime();
};

// 设置错误提示并清空成功提示
const setError = (message) => {
  error.value = message || '';
  if (message) {
    success.value = '';
  }
};

// 设置成功提示并清空错误提示
const setSuccess = (message) => {
  success.value = message || '';
  if (message) {
    error.value = '';
  }
};

const DEFAULT_PROVINCES = [
  '北京', '天津', '上海', '重庆',
  '河北', '山西', '辽宁', '吉林', '黑龙江',
  '江苏', '浙江', '安徽', '福建', '江西', '山东',
  '河南', '湖北', '湖南', '广东', '海南',
  '四川', '贵州', '云南', '陕西', '甘肃', '青海',
  '内蒙古', '广西', '西藏', '宁夏', '新疆'
];

const provinceOptions = computed(() => {
  const dynamic = Array.isArray(fuelStore.oilPayload?.provinces)
    ? fuelStore.oilPayload.provinces
      .map((item) => String(item?.region_name || '').trim())
      .filter(Boolean)
    : [];

  const set = new Set([...DEFAULT_PROVINCES, ...dynamic]);
  return Array.from(set);
});

const cacheHint = computed(() => {
  if (!fuelStore.lastOilFetchDate) return '';
  return `油价缓存日期：${fuelStore.lastOilFetchDate}（每日自动更新一次）`;
});

const locationHint = computed(() => {
  if (!fuelStore.regionName) return '';
  const sourceMap = {
    geolocation: 'GPS定位',
    ip: 'IP定位',
    manual: '手动地区'
  };
  return `当前地区：${fuelStore.regionName}（${sourceMap[fuelStore.locationSource] || '未知来源'}）`;
});

const form = ref({
  region_name: fuelStore.regionName || '青海省',
  fuel_type: fuelStore.selectedFuelType || '92号汽油',
  price: fuelStore.currentFuelPrice || 0,
  effective_date: today(),
  selected_date: today()
});

const selectedRegionKey = computed(() => normalizeProvinceName(form.value.region_name));

const filteredPrices = computed(() => {
  const endDate = form.value.selected_date || today();
  const selectedRegion = selectedRegionKey.value;
  return prices.value.filter((item) => {
    const effectiveDate = item?.effective_date;
    if (!effectiveDate) return false;
    const rowRegion = normalizeProvinceName(item?.region_name || '');
    if (selectedRegion && rowRegion && rowRegion !== selectedRegion) return false;
    return effectiveDate <= endDate;
  });
});

// 将后端记录规整为日期x油品的折线图序列
const buildSeriesData = () => {
  const dedup = new Map();
  const fuelTypes = ['92号汽油', '95号汽油', '98号汽油', '0号柴油'];

  for (const item of filteredPrices.value) {
    const fuelType = item?.fuel_type;
    const dateKey = item?.effective_date;
    const priceValue = Number(item?.price);
    if (!fuelType || !dateKey || !Number.isFinite(priceValue)) continue;

    const key = `${dateKey}__${fuelType}`;
    const previous = dedup.get(key);
    if (!previous) {
      dedup.set(key, item);
      continue;
    }

    const previousTime = new Date(previous.created_at || 0).getTime();
    const currentTime = new Date(item.created_at || 0).getTime();
    if (currentTime >= previousTime) {
      dedup.set(key, item);
    }
  }

  const dateSet = new Set();
  const dataByDate = new Map();
  for (const item of dedup.values()) {
    const dateKey = item.effective_date;
    const fuelType = item.fuel_type;
    const priceValue = Number(item.price);
    dateSet.add(dateKey);
    if (!dataByDate.has(dateKey)) {
      dataByDate.set(dateKey, {});
    }
    dataByDate.get(dateKey)[fuelType] = priceValue;
  }

  const dates = [...dateSet].sort((a, b) => new Date(a).getTime() - new Date(b).getTime());
  const visibleDates = dates.length > MAX_POINTS ? dates.slice(-MAX_POINTS) : dates;
  const series = fuelTypes.map((fuelType) => ({
    name: fuelType,
    type: 'line',
    smooth: true,
    connectNulls: false,
    symbol: 'circle',
    symbolSize: 7,
    data: visibleDates.map((dateKey) => {
      const value = dataByDate.get(dateKey)?.[fuelType];
      return Number.isFinite(value) ? value : null;
    })
  }));

  return { dates: visibleDates, series };
};

const chartData = computed(() => buildSeriesData());

// 渲染油价折线图实例（同一实例重复 setOption）。
const renderChart = async () => {
  await nextTick();
  if (!chartRef.value || !prices.value.length) {
    if (chartInstance) {
      chartInstance.dispose();
      chartInstance = null;
    }
    return;
  }

  const { dates, series } = chartData.value;
  if (!dates.length) {
    if (chartInstance) {
      chartInstance.dispose();
      chartInstance = null;
    }
    return;
  }

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      top: 0
    },
    grid: {
      left: 50,
      right: 20,
      top: 42,
      bottom: 40
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        rotate: dates.length > 8 ? 30 : 0
      }
    },
    yAxis: {
      type: 'value',
      name: '元/升'
    },
    series
  });
};

// 响应窗口变化重绘图表，保证移动端可读性。
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize();
  }
};

// 获取后端已保存的油价记录
const fetchPrices = async () => {
  try {
    const res = await axios.get('/api/trips/fuel-prices', {
      params: {
        region_name: form.value.region_name,
        limit: 500
      }
    });
    prices.value = res.data.data || [];
  } catch (err) {
    setError(err.response?.data?.message || '获取油价失败');
  }
};

// 将Store中的当前油价同步到表单
const syncPriceFromStore = () => {
  if (fuelStore.currentFuelPrice !== null && fuelStore.currentFuelPrice !== undefined) {
    form.value.price = fuelStore.currentFuelPrice;
  }
  form.value.effective_date = today();
};

// 按当前地区与油品拉取当日油价
const fetchDailyOilPrice = async ({ force = false } = {}) => {
  try {
    setError('');
    setSuccess('');
    fuelStore.setRegionName(form.value.region_name);
    fuelStore.setFuelType(form.value.fuel_type);

    await fuelStore.fetchOilPrice({
      force,
      customRegionName: form.value.region_name
    });

    form.value.region_name = fuelStore.regionName;
    syncPriceFromStore();
    setSuccess(`已更新${form.value.region_name}${form.value.fuel_type}油价：${form.value.price} 元/升`);

    // 价格先展示，入库与历史刷新放到后台异步执行，提升交互速度。
    Promise.resolve()
      .then(async () => {
        await fuelStore.syncOilPriceToBackend();
        await fetchPrices();
      })
      .catch((syncErr) => {
        const message = syncErr?.response?.data?.message || syncErr?.message || '油价已更新，但同步数据库失败';
        setError(message);
      });
  } catch (err) {
    setError(fuelStore.lastError || err.response?.data?.message || '获取地区油价失败');
  }
};

// 下拉选择地区后立即刷新油价，避免仅依赖 watch 导致触发时机不稳定。
const onRegionChange = async (value) => {
  const nextRegion = String(value || '').trim();
  if (!nextRegion) return;
  form.value.region_name = nextRegion;
  fuelStore.setRegionName(nextRegion);
  await fetchDailyOilPrice();
};

watch(() => form.value.fuel_type, async (value) => {
  fuelStore.setFuelType(value);
  if (fuelStore.oilPayload) {
    syncPriceFromStore();
    return;
  }
  await fetchDailyOilPrice();
});

watch(() => form.value.region_name, (value, oldValue) => {
  if (!value) return;
  fuelStore.setRegionName(value);
  const nextRegion = String(value || '').trim();
  const prevRegion = String(oldValue || '').trim();
  if (!nextRegion || nextRegion === prevRegion) return;
});

watch(() => form.value.selected_date, async () => {
  await renderChart();
});

onMounted(async () => {
  await fetchPrices();
  form.value.fuel_type = fuelStore.selectedFuelType;
  form.value.region_name = fuelStore.regionName;
  try {
    await fuelStore.initializeDailyOilPrice();
    // 初始化优先命中 Pinia 缓存，非当日缓存才请求后端代理接口。
    await fetchDailyOilPrice();
    setSuccess(`已加载${fuelStore.regionName}${fuelStore.selectedFuelType}当日油价`);
  } catch (err) {
    setError(fuelStore.lastError || err.response?.data?.message || '初始化油价失败');
  }
  form.value.region_name = fuelStore.regionName;
  syncPriceFromStore();
  await renderChart();
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});

watch(prices, async () => {
  await renderChart();
}, { deep: true });

watch(filteredPrices, async () => {
  await renderChart();
}, { deep: true });

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

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
  background: #f8faf5;
  border: 1px solid #e3ead6;
  border-radius: 10px;
  padding: 0.9rem 1.1rem;
}

.title {
  font-weight: 700;
  font-size: 1.2rem;
  color: #2d3436;
}

.hint {
  color: #667459;
}

.mb {
  margin-bottom: 12px;
}

.form {
  margin-bottom: 12px;
  max-width: 480px;
}

.form :deep(.el-select) {
  width: 100%;
}

.range-hint {
  font-size: 12px;
  color: #7a8770;
  margin-top: 6px;
}

.chart-block {
  border: 1px solid #dfe6d2;
  background: #ffffff;
  border-radius: 8px;
  padding: 10px 12px;
}

.chart-title {
  font-weight: 700;
  color: #2d3436;
  margin-bottom: 8px;
}

.chart {
  height: 360px;
  width: 100%;
}

.chart-empty {
  color: #7a8770;
  font-size: 14px;
  padding: 12px 0;
}

.info-note {
  border: 1px solid #dfe6d2;
  background: #f7faef;
  border-radius: 8px;
  padding: 10px 12px;
}

.info-note-title {
  font-weight: 700;
  color: #2d3436;
  margin-bottom: 2px;
}

.info-note-text {
  color: #4d5b44;
  line-height: 1.5;
}
</style>
