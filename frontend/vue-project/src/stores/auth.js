/** auth：登录态与用户信息持久化管理 */
import { computed, ref } from 'vue';
import { defineStore } from 'pinia';

const TOKEN_KEY = 'token';
const USER_KEY = 'user';
const MODE_KEY = 'auth_storage_mode';

export const useAuthStore = defineStore('auth', () => {
  const token = ref('');
  const user = ref(null);
  const persistenceMode = ref('local');

  const isLoggedIn = computed(() => !!token.value);

  // 从本地存储恢复 token 与用户信息
  const hydrate = () => {
    if (typeof window === 'undefined') return;
    const mode = localStorage.getItem(MODE_KEY) || 'local';
    persistenceMode.value = mode;
    if (mode === 'session') {
      token.value = sessionStorage.getItem(TOKEN_KEY) || '';
      const raw = sessionStorage.getItem(USER_KEY);
      user.value = raw ? JSON.parse(raw) : null;
      return;
    }
    token.value = localStorage.getItem(TOKEN_KEY) || '';
    const raw = localStorage.getItem(USER_KEY);
    user.value = raw ? JSON.parse(raw) : null;
  };

  // 将当前登录态写入本地存储
  const persist = () => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(MODE_KEY, persistenceMode.value);
    if (persistenceMode.value === 'session') {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      if (token.value) sessionStorage.setItem(TOKEN_KEY, token.value);
      else sessionStorage.removeItem(TOKEN_KEY);
      if (user.value) sessionStorage.setItem(USER_KEY, JSON.stringify(user.value));
      else sessionStorage.removeItem(USER_KEY);
      return;
    }

    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    if (token.value) localStorage.setItem(TOKEN_KEY, token.value);
    else localStorage.removeItem(TOKEN_KEY);
    if (user.value) localStorage.setItem(USER_KEY, JSON.stringify(user.value));
    else localStorage.removeItem(USER_KEY);
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
    token.value = '';
    user.value = null;
    localStorage.removeItem(MODE_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    persist();
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
    setUser
  };
});
