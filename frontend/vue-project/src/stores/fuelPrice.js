import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios';

const STORAGE_KEY = 'fuel-price-store-v1';

const fuelFieldMap = {
  '92号汽油': 'n92',
  '95号汽油': 'n95',
  '98号汽油': 'n98',
  '0号柴油': 'n0'
};

const normalizeRegionName = (value) => {
  if (!value || typeof value !== 'string') return '';
  const trimmed = value.trim();
  if (!trimmed) return '';
  if (trimmed.endsWith('省') || trimmed.endsWith('市') || trimmed.endsWith('自治区')) return trimmed;
  return `${trimmed}省`;
};

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

const getToday = () => new Date().toISOString().slice(0, 10);

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

  const setRegionName = (value) => {
    regionName.value = normalizeRegionName(value) || regionName.value;
    locationSource.value = 'manual';
    persist();
  };

  const setFuelType = (fuelType) => {
    if (!fuelFieldMap[fuelType]) return;
    selectedFuelType.value = fuelType;
    persist();
  };

  const needFetchToday = computed(() => lastOilFetchDate.value !== getToday());

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

  const detectRegionByIP = async () => {
    const res = await axios.get('https://ipapi.co/json/');
    const detected = normalizeRegionName(res.data?.region || res.data?.region_name || '');
    if (!detected) throw new Error('未识别到地区');
    regionName.value = detected;
    locationSource.value = 'ip';
    persist();
    return detected;
  };

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

  const initializeDailyOilPrice = async () => {
    hydrate();
    await detectRegion();
    await fetchOilPrice();
    return {
      regionName: regionName.value,
      price: currentFuelPrice.value
    };
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
    initializeDailyOilPrice
  };
});