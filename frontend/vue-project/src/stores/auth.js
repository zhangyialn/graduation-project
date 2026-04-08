/** auth：登录态与用户信息持久化管理 */
import { computed, ref } from 'vue';
import { defineStore } from 'pinia';

const TOKEN_KEY = 'token';
const USER_KEY = 'user';
const MODE_KEY = 'auth_storage_mode';
const TAB_ID_KEY = 'dev_auth_tab_id';
const IS_DEV = import.meta.env.DEV;

const getTabId = () => {
  if (typeof window === 'undefined') return 'server';
  let tabId = sessionStorage.getItem(TAB_ID_KEY);
  if (!tabId) {
    tabId = `tab_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    sessionStorage.setItem(TAB_ID_KEY, tabId);
  }
  return tabId;
};

const getStorageKeys = () => {
  if (!IS_DEV) {
    return {
      tokenKey: TOKEN_KEY,
      userKey: USER_KEY,
      modeKey: MODE_KEY
    };
  }

  const tabId = getTabId();
  return {
    tokenKey: `${TOKEN_KEY}:${tabId}`,
    userKey: `${USER_KEY}:${tabId}`,
    modeKey: `${MODE_KEY}:${tabId}`
  };
};

export const useAuthStore = defineStore('auth', () => {
  const token = ref('');
  const user = ref(null);
  const persistenceMode = ref('local');

  const isLoggedIn = computed(() => !!token.value);

  // 从本地存储恢复 token 与用户信息
  const hydrate = () => {
    if (typeof window === 'undefined') return;
    const keys = getStorageKeys();
    const mode = localStorage.getItem(keys.modeKey) || (IS_DEV ? 'session' : 'local');
    persistenceMode.value = mode;

    const parseUser = (raw) => {
      if (!raw) return null;
      try {
        return JSON.parse(raw);
      } catch (_err) {
        return null;
      }
    };

    if (mode === 'session') {
      token.value = sessionStorage.getItem(keys.tokenKey) || '';
      const raw = sessionStorage.getItem(keys.userKey);
      user.value = parseUser(raw);
      return;
    }

    token.value = localStorage.getItem(keys.tokenKey) || '';
    const raw = localStorage.getItem(keys.userKey);
    user.value = parseUser(raw);
  };

  // 将当前登录态写入本地存储
  const persist = () => {
    if (typeof window === 'undefined') return;
    const keys = getStorageKeys();

    localStorage.setItem(keys.modeKey, persistenceMode.value);
    if (persistenceMode.value === 'session') {
      localStorage.removeItem(keys.tokenKey);
      localStorage.removeItem(keys.userKey);
      if (token.value) sessionStorage.setItem(keys.tokenKey, token.value);
      else sessionStorage.removeItem(keys.tokenKey);
      if (user.value) sessionStorage.setItem(keys.userKey, JSON.stringify(user.value));
      else sessionStorage.removeItem(keys.userKey);
      return;
    }

    sessionStorage.removeItem(keys.tokenKey);
    sessionStorage.removeItem(keys.userKey);
    if (token.value) localStorage.setItem(keys.tokenKey, token.value);
    else localStorage.removeItem(keys.tokenKey);
    if (user.value) localStorage.setItem(keys.userKey, JSON.stringify(user.value));
    else localStorage.removeItem(keys.userKey);
  };

  // 设置完整会话（登录后调用）
  const setSession = (nextToken, nextUser, mode = 'local') => {
    persistenceMode.value = mode === 'session' ? 'session' : 'local';
    token.value = nextToken || '';
    user.value = nextUser || null;
    persist();
  };

  // 清空会话（退出登录时调用）
  const clearSession = () => {
    const keys = getStorageKeys();
    token.value = '';
    user.value = null;
    persistenceMode.value = IS_DEV ? 'session' : 'local';

    localStorage.removeItem(keys.tokenKey);
    localStorage.removeItem(keys.userKey);
    localStorage.removeItem(keys.modeKey);

    sessionStorage.removeItem(keys.tokenKey);
    sessionStorage.removeItem(keys.userKey);
  };

  // 兼容旧代码调用名
  const clearToken = () => {
    clearSession();
  };

  // 仅更新用户信息并持久化
  const setUser = (nextUser) => {
    user.value = nextUser || null;
    persist();
  };

  return {
    token,
    user,
    persistenceMode,
    isLoggedIn,
    hydrate,
    setSession,
    clearSession,
    clearToken,
    setUser
  };
});
