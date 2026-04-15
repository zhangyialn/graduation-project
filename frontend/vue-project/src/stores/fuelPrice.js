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

const provinceSuffixRegexp = /(省|市|自治区|特别行政区|壮族自治区|回族自治区|维吾尔自治区)$/;

// 规范化地区名称，保证后端接口可识别
const normalizeRegionName = (value) => {
  if (!value || typeof value !== 'string') return '';
  const trimmed = value.trim();
  if (!trimmed) return '';
  return trimmed;
};

// 规范化定位 keyword（城市优先），用于第三方油价查询。
const normalizeLocationKeyword = (value) => normalizeRegionName(value);

const normalizeProvinceName = (value) => normalizeRegionName(value).replace(provinceSuffixRegexp, '');

const pickProvinceByKeyword = (provinceRows, keyword) => {
  if (!Array.isArray(provinceRows) || provinceRows.length === 0) return null;
  const target = normalizeProvinceName(keyword);
  if (!target) return provinceRows[0];

  const exact = provinceRows.find((row) => normalizeProvinceName(row.region_name) === target);
  if (exact) return exact;

  const fuzzy = provinceRows.find((row) => normalizeProvinceName(row.region_name).includes(target) || target.includes(normalizeProvinceName(row.region_name)));
  return fuzzy || provinceRows[0];
};

// 适配 guiguiya 油价接口返回结构，合并四种油品为统一 payload。
const pickOilPayload = (rawByFuel, keyword = '') => {
  if (!rawByFuel || typeof rawByFuel !== 'object') return null;

  const provinces = new Map();
  let effectiveDate = '';

  for (const fuelField of Object.keys(reverseFuelFieldMap)) {
    const raw = rawByFuel[fuelField];
    if (!raw || Number(raw.code) !== 200 || !raw.data || typeof raw.data !== 'object') {
      continue;
    }

    if (!effectiveDate && isValidEffectiveDate(raw.update_time)) {
      effectiveDate = raw.update_time;
    }

    Object.entries(raw.data).forEach(([province, price]) => {
      const normalizedProvince = normalizeRegionName(province);
      if (!normalizedProvince) return;
      if (!provinces.has(normalizedProvince)) {
        provinces.set(normalizedProvince, {
          region_name: normalizedProvince,
          n92: null,
          n95: null,
          n98: null,
          n0: null
        });
      }
      const row = provinces.get(normalizedProvince);
      const numeric = Number(price);
      row[fuelField] = Number.isFinite(numeric) ? numeric : null;
    });
  }

  const provinceRows = Array.from(provinces.values());
  if (!provinceRows.length) return null;

  const selected = pickProvinceByKeyword(provinceRows, keyword);
  if (!selected) return null;

  return {
    regionName: selected.region_name,
    keyword: normalizeRegionName(keyword),
    n92: selected.n92,
    n95: selected.n95,
    n98: selected.n98,
    n0: selected.n0,
    date: effectiveDate || '',
    provinces: provinceRows
  };
};

// 判断接口返回的发布日期是否可作为 YYYY-MM-DD 入库。
const isValidEffectiveDate = (value) => /^\d{4}-\d{2}-\d{2}$/.test(String(value || '').trim());

// 获取当天日期字符串
const getToday = () => getBeijingDateKey();

// 从逆地理编码结果中提取油价查询 keyword（城市优先）
const getKeywordFromReverseGeo = (payload) => {
  const candidates = [
    payload?.city,
    payload?.locality,
    payload?.localityInfo?.administrative?.[2]?.name,
    payload?.principalSubdivision,
    payload?.localityInfo?.administrative?.[1]?.name,
    payload?.localityInfo?.administrative?.[0]?.name
  ];
  return normalizeLocationKeyword(candidates.find(Boolean) || '');
};

// 从逆地理编码结果中提取展示地区名称（省份优先）
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
  const locationKeyword = ref('');
  const selectedFuelType = ref('92号汽油');
  const oilPayload = ref(null);
  const lastOilFetchDate = ref('');
  const lastOilFetchAt = ref('');
  const lastBackendSyncDate = ref('');
  const locationSource = ref('manual');
  const coords = ref(null);
  const loadingOil = ref(false);
  const loadingLocation = ref(false);
  const lastError = ref('');

  const currentFuelField = computed(() => fuelFieldMap[selectedFuelType.value] || 'n92');
  const currentFuelPrice = computed(() => {
    if (!oilPayload.value) return null;
    const provinceRows = Array.isArray(oilPayload.value?.provinces) ? oilPayload.value.provinces : [];
    const selectedRow = pickProvinceByKeyword(provinceRows, regionName.value || locationKeyword.value || '');
    const value = Number(selectedRow?.[currentFuelField.value] ?? oilPayload.value[currentFuelField.value]);
    return Number.isFinite(value) ? value : null;
  });

  // 持久化油价与定位相关状态
  const persist = () => {
    if (typeof window === 'undefined') return;
    const snapshot = {
      regionName: regionName.value,
      locationKeyword: locationKeyword.value,
      selectedFuelType: selectedFuelType.value,
      oilPayload: oilPayload.value,
      lastOilFetchDate: lastOilFetchDate.value,
      lastOilFetchAt: lastOilFetchAt.value,
      lastBackendSyncDate: lastBackendSyncDate.value,
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
      locationKeyword.value = data.locationKeyword || locationKeyword.value;
      selectedFuelType.value = data.selectedFuelType || selectedFuelType.value;
      oilPayload.value = data.oilPayload || null;
      lastOilFetchDate.value = data.lastOilFetchDate || '';
      lastOilFetchAt.value = data.lastOilFetchAt || '';
      lastBackendSyncDate.value = data.lastBackendSyncDate || '';
      locationSource.value = data.locationSource || 'manual';
      coords.value = data.coords || null;
    } catch (_e) {
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  // 设置地区名称并标记为手动来源
  const setRegionName = (value) => {
    const normalized = normalizeRegionName(value);
    regionName.value = normalized || regionName.value;
    // 手动输入地区时，同步覆盖 keyword，确保查询词与用户输入一致。
    locationKeyword.value = normalizeLocationKeyword(normalized) || locationKeyword.value;
    locationSource.value = 'manual';

    // 若当天缓存里已包含该省份，切换地区时直接使用缓存，不触发额外请求。
    if (oilPayload.value && Array.isArray(oilPayload.value?.provinces)) {
      const matched = pickProvinceByKeyword(oilPayload.value.provinces, normalized || locationKeyword.value);
      if (matched?.region_name) {
        regionName.value = matched.region_name;
      }
    }

    persist();
  };

  // 设置当前油品类型
  const setFuelType = (fuelType) => {
    if (!fuelFieldMap[fuelType]) return;
    selectedFuelType.value = fuelType;
    persist();
  };

  const needFetchToday = computed(() => lastOilFetchDate.value !== getToday());

  // 判断指定地区是否可以直接命中当日缓存。
  const canUseCachedRegion = (keyword) => {
    if (needFetchToday.value || !oilPayload.value) return false;
    const provinceRows = Array.isArray(oilPayload.value?.provinces) ? oilPayload.value.provinces : [];
    if (!provinceRows.length) return true;
    const matched = pickProvinceByKeyword(provinceRows, keyword || regionName.value || locationKeyword.value);
    return !!matched;
  };

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

    const detectedRegion = getRegionFromReverseGeo(reverse.data);
    const detectedKeyword = getKeywordFromReverseGeo(reverse.data) || detectedRegion;
    if (!detectedRegion && !detectedKeyword) throw new Error('定位成功但未解析到地区');

    regionName.value = detectedRegion || detectedKeyword || regionName.value;
    locationKeyword.value = detectedKeyword || detectedRegion || locationKeyword.value;
    locationSource.value = 'geolocation';
    persist();
    return regionName.value;
  };

  // 浏览器定位失败时回退为IP定位
  const detectRegionByIP = async () => {
    const res = await axios.get('https://ipapi.co/json/');
    const detectedKeyword = normalizeLocationKeyword(res.data?.city || res.data?.region || res.data?.region_name || '');
    const detectedRegion = normalizeRegionName(res.data?.region || res.data?.region_name || detectedKeyword);
    if (!detectedRegion && !detectedKeyword) throw new Error('未识别到地区');
    regionName.value = detectedRegion || detectedKeyword || regionName.value;
    locationKeyword.value = detectedKeyword || detectedRegion || locationKeyword.value;
    locationSource.value = 'ip';
    persist();
    return regionName.value;
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
    const customKeyword = normalizeLocationKeyword(customRegionName);
    const targetKeyword = customKeyword || locationKeyword.value || regionName.value;
    if (!targetKeyword) {
      throw new Error('缺少定位关键词，无法获取油价');
    }

    if (!force && canUseCachedRegion(targetKeyword)) {
      const provinceRows = Array.isArray(oilPayload.value?.provinces) ? oilPayload.value.provinces : [];
      const matched = pickProvinceByKeyword(provinceRows, targetKeyword);
      if (matched?.region_name) {
        regionName.value = matched.region_name;
      }
      locationKeyword.value = normalizeLocationKeyword(targetKeyword) || locationKeyword.value;
      persist();
      return oilPayload.value;
    }

    loadingOil.value = true;
    lastError.value = '';
    try {
      const res = await axios.get('/api/trips/external-oil-prices', {
        params: { keyword: targetKeyword }
      });

      const payload = pickOilPayload(res.data?.data || {}, targetKeyword);
      if (!payload) {
        throw new Error(res?.data?.message || '油价接口返回无效数据');
      }

      oilPayload.value = payload;
      locationKeyword.value = normalizeLocationKeyword(payload.keyword || targetKeyword) || targetKeyword;
      regionName.value = normalizeRegionName(payload.regionName || payload.keyword || targetKeyword) || regionName.value;
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
    if (!locationKeyword.value && !regionName.value) {
      await detectRegion();
    } else if (!locationKeyword.value && regionName.value) {
      locationKeyword.value = regionName.value;
      persist();
    }

    if (needFetchToday.value || !oilPayload.value) {
      await fetchOilPrice();
    }

    return {
      regionName: regionName.value,
      price: currentFuelPrice.value
    };
  };

  // 将当前油价写入后端 fuel_prices（按油品逐条upsert）
  const syncOilPriceToBackend = async ({ force = false } = {}) => {
    if (!oilPayload.value) return;
    const effectiveDate = isValidEffectiveDate(oilPayload.value?.date)
      ? oilPayload.value.date
      : getToday();

    // 同一天已完成过入库时直接跳过，避免每次切地区都全量写库。
    if (!force && lastBackendSyncDate.value === effectiveDate) {
      return;
    }

    const source = `frontend-oil-api:${regionName.value || '未知地区'}`;

    const provinceRows = Array.isArray(oilPayload.value?.provinces) && oilPayload.value.provinces.length
      ? oilPayload.value.provinces
      : [{
        region_name: regionName.value || '未知省份',
        n92: oilPayload.value?.n92,
        n95: oilPayload.value?.n95,
        n98: oilPayload.value?.n98,
        n0: oilPayload.value?.n0
      }];

    const entries = provinceRows.flatMap((provinceRow) => Object.entries(reverseFuelFieldMap)
      .map(([field, fuelType]) => {
        const price = Number(provinceRow?.[field]);
        if (!Number.isFinite(price)) return null;
        return {
          region_name: normalizeRegionName(provinceRow.region_name || regionName.value || '未知省份'),
          fuel_type: fuelType,
          price
        };
      })
      .filter(Boolean));

    if (!entries.length) return;

    await axios.post('/api/trips/fuel-prices/batch', {
      effective_date: effectiveDate,
      source,
      items: entries
    });

    lastBackendSyncDate.value = effectiveDate;
    persist();
  };

  hydrate();

  return {
    regionName,
    locationKeyword,
    selectedFuelType,
    oilPayload,
    lastOilFetchDate,
    lastOilFetchAt,
    lastBackendSyncDate,
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
