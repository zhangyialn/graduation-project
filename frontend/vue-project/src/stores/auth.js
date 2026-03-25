/** auth：登录态与用户信息持久化管理 */
import { computed, ref } from 'vue';
import { defineStore } from 'pinia';

const TOKEN_KEY = 'token';
const USER_KEY = 'user';

export const useAuthStore = defineStore('auth', () => {
  const token = ref('');
  const user = ref(null);

  const isLoggedIn = computed(() => !!token.value);

  // 从本地存储恢复 token 与用户信息
  const hydrate = () => {
    if (typeof window === 'undefined') return;
    token.value = localStorage.getItem(TOKEN_KEY) || '';
    const raw = localStorage.getItem(USER_KEY);
    user.value = raw ? JSON.parse(raw) : null;
  };

  // 将当前登录态写入本地存储
  const persist = () => {
    if (typeof window === 'undefined') return;
    if (token.value) localStorage.setItem(TOKEN_KEY, token.value);
    else localStorage.removeItem(TOKEN_KEY);

    if (user.value) localStorage.setItem(USER_KEY, JSON.stringify(user.value));
    else localStorage.removeItem(USER_KEY);
  };

  // 设置完整会话（登录后调用）
  const setSession = (nextToken, nextUser) => {
    token.value = nextToken || '';
    user.value = nextUser || null;
    persist();
  };

  // 清空会话（退出登录时调用）
  const clearSession = () => {
    token.value = '';
    user.value = null;
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
    isLoggedIn,
    hydrate,
    setSession,
    clearSession,
    setUser
  };
});
