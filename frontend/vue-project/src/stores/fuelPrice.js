/** fuelPrice：地区定位与当日油价缓存 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios';
import { getBeijingDateKey } from '../utils/datetime';

const STORAGE_KEY = 'fuel-price-store-v1';

const fuelFieldMap = {
  '92号汽油': 'n92',
  '95号汽油': 'n95',
  '98号汽油': 'n98',
  '0号柴油': 'n0'
};

const reverseFuelFieldMap = {
  n92: '92号汽油',
  n95: '95号汽油',
  n98: '98号汽油',
  n0: '0号柴油'
};

// 规范化地区名称，保证后端接口可识别
const normalizeRegionName = (value) => {
  if (!value || typeof value !== 'string') return '';
  const trimmed = value.trim();
  if (!trimmed) return '';
  if (trimmed.endsWith('省') || trimmed.endsWith('市') || trimmed.endsWith('自治区')) return trimmed;
  return `${trimmed}省`;
};

// 兼容多种第三方接口返回结构并提取油价数据
const pickOilPayload = (raw) => {
  if (!raw) return null;
  if (Array.isArray(raw)) return raw[0] || null;
  if (Array.isArray(raw.data)) return raw.data[0] || null;
  if (raw.data && typeof raw.data === 'object') return raw.data;
  if (Array.isArray(raw.result)) return raw.result[0] || null;
  if (raw.result && typeof raw.result === 'object') return raw.result;
  if (raw.n92 || raw.n95 || raw.n98 || raw.n0) return raw;
  return null;
};

// 获取当天日期字符串
const getToday = () => getBeijingDateKey();

// 从逆地理编码结果中提取地区名称
const getRegionFromReverseGeo = (payload) => {
  const candidates = [
    payload?.principalSubdivision,
    payload?.localityInfo?.administrative?.[1]?.name,
    payload?.localityInfo?.administrative?.[0]?.name,
    payload?.city,
    payload?.locality
  ];
  return normalizeRegionName(candidates.find(Boolean) || '');
};

export const useFuelPriceStore = defineStore('fuelPrice', () => {
  const regionName = ref('青海省');
  const selectedFuelType = ref('92号汽油');
  const oilPayload = ref(null);
  const lastOilFetchDate = ref('');
  const lastOilFetchAt = ref('');
  const locationSource = ref('manual');
  const coords = ref(null);
  const loadingOil = ref(false);
  const loadingLocation = ref(false);
  const lastError = ref('');

  const currentFuelField = computed(() => fuelFieldMap[selectedFuelType.value] || 'n92');
  const currentFuelPrice = computed(() => {
    if (!oilPayload.value) return null;
    const value = Number(oilPayload.value[currentFuelField.value]);
    return Number.isFinite(value) ? value : null;
  });

  // 持久化油价与定位相关状态
  const persist = () => {
    if (typeof window === 'undefined') return;
    const snapshot = {
      regionName: regionName.value,
      selectedFuelType: selectedFuelType.value,
      oilPayload: oilPayload.value,
      lastOilFetchDate: lastOilFetchDate.value,
      lastOilFetchAt: lastOilFetchAt.value,
      locationSource: locationSource.value,
      coords: coords.value
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
  };

  // 从本地恢复油价与定位状态
  const hydrate = () => {
    if (typeof window === 'undefined') return;
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      const data = JSON.parse(raw);
      regionName.value = data.regionName || regionName.value;
      selectedFuelType.value = data.selectedFuelType || selectedFuelType.value;
      oilPayload.value = data.oilPayload || null;
      lastOilFetchDate.value = data.lastOilFetchDate || '';
      lastOilFetchAt.value = data.lastOilFetchAt || '';
      locationSource.value = data.locationSource || 'manual';
      coords.value = data.coords || null;
    } catch (_e) {
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  // 设置地区名称并标记为手动来源
  const setRegionName = (value) => {
    regionName.value = normalizeRegionName(value) || regionName.value;
    locationSource.value = 'manual';
    persist();
  };

  // 设置当前油品类型
  const setFuelType = (fuelType) => {
    if (!fuelFieldMap[fuelType]) return;
    selectedFuelType.value = fuelType;
    persist();
  };

  const needFetchToday = computed(() => lastOilFetchDate.value !== getToday());

  // 优先使用浏览器定位识别地区
  const detectRegionByGeolocation = async () => {
    if (!navigator.geolocation) throw new Error('当前浏览器不支持定位');
    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: false,
        timeout: 8000,
        maximumAge: 300000
      });
    });

    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;
    coords.value = { latitude, longitude };

    const reverse = await axios.get('https://api.bigdatacloud.net/data/reverse-geocode-client', {
      params: {
        latitude,
        longitude,
        localityLanguage: 'zh'
      }
    });

    const detected = getRegionFromReverseGeo(reverse.data);
    if (!detected) throw new Error('定位成功但未解析到地区');

    regionName.value = detected;
    locationSource.value = 'geolocation';
    persist();
    return detected;
  };

  // 浏览器定位失败时回退为IP定位
  const detectRegionByIP = async () => {
    const res = await axios.get('https://ipapi.co/json/');
    const detected = normalizeRegionName(res.data?.region || res.data?.region_name || '');
    if (!detected) throw new Error('未识别到地区');
    regionName.value = detected;
    locationSource.value = 'ip';
    persist();
    return detected;
  };

  // 自动识别地区（GPS优先，IP兜底）
  const detectRegion = async () => {
    loadingLocation.value = true;
    lastError.value = '';
    try {
      return await detectRegionByGeolocation();
    } catch (_geoErr) {
      try {
        return await detectRegionByIP();
      } catch (ipErr) {
        lastError.value = ipErr?.message || '自动定位失败';
        return regionName.value;
      }
    } finally {
      loadingLocation.value = false;
    }
  };

  // 拉取并缓存指定地区当日油价
  const fetchOilPrice = async ({ force = false, customRegionName = '' } = {}) => {
    const targetRegion = normalizeRegionName(customRegionName) || regionName.value;
    if (!targetRegion) {
      throw new Error('缺少地区，无法获取油价');
    }

    if (!force && !needFetchToday.value && oilPayload.value && targetRegion === regionName.value) {
      return oilPayload.value;
    }

    loadingOil.value = true;
    lastError.value = '';
    try {
      const res = await axios.get('https://v2.xxapi.cn/api/oilPrice', {
        params: {
          regionName: targetRegion
        }
      });
      const payload = pickOilPayload(res.data);
      if (!payload) {
        throw new Error('油价接口返回无效数据');
      }

      oilPayload.value = payload;
      regionName.value = normalizeRegionName(payload.regionName || targetRegion) || targetRegion;
      lastOilFetchDate.value = getToday();
      lastOilFetchAt.value = new Date().toISOString();
      persist();
      return payload;
    } catch (err) {
      lastError.value = err.response?.data?.message || err.message || '获取油价失败';
      throw err;
    } finally {
      loadingOil.value = false;
    }
  };

  // 页面启动时初始化地区与当日油价
  const initializeDailyOilPrice = async () => {
    hydrate();
    await detectRegion();
    await fetchOilPrice();
    return {
      regionName: regionName.value,
      price: currentFuelPrice.value
    };
  };

  // 将当前油价写入后端 fuel_prices（按油品逐条upsert）
  const syncOilPriceToBackend = async () => {
    if (!oilPayload.value) return;
    const effectiveDate = getToday();
    const source = `frontend-oil-api:${regionName.value || '未知地区'}`;

    const entries = Object.entries(reverseFuelFieldMap)
      .map(([field, fuelType]) => {
        const price = Number(oilPayload.value?.[field]);
        return Number.isFinite(price) ? { fuelType, price } : null;
      })
      .filter(Boolean);

    for (const item of entries) {
      await axios.post('/api/trips/fuel-prices', {
        fuel_type: item.fuelType,
        price: item.price,
        effective_date: effectiveDate,
        source
      });
    }
  };

  hydrate();

  return {
    regionName,
    selectedFuelType,
    oilPayload,
    lastOilFetchDate,
    lastOilFetchAt,
    locationSource,
    coords,
    loadingOil,
    loadingLocation,
    lastError,
    currentFuelPrice,
    needFetchToday,
    setRegionName,
    setFuelType,
    detectRegion,
    fetchOilPrice,
    initializeDailyOilPrice,
    syncOilPriceToBackend
  };
});
