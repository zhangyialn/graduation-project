import { computed, ref } from 'vue';
import { defineStore } from 'pinia';

const TOKEN_KEY = 'token';
const USER_KEY = 'user';

export const useAuthStore = defineStore('auth', () => {
  const token = ref('');
  const user = ref(null);

  const isLoggedIn = computed(() => !!token.value);

  const hydrate = () => {
    if (typeof window === 'undefined') return;
    token.value = localStorage.getItem(TOKEN_KEY) || '';
    const raw = localStorage.getItem(USER_KEY);
    user.value = raw ? JSON.parse(raw) : null;
  };

  const persist = () => {
    if (typeof window === 'undefined') return;
    if (token.value) localStorage.setItem(TOKEN_KEY, token.value);
    else localStorage.removeItem(TOKEN_KEY);

    if (user.value) localStorage.setItem(USER_KEY, JSON.stringify(user.value));
    else localStorage.removeItem(USER_KEY);
  };

  const setSession = (nextToken, nextUser) => {
    token.value = nextToken || '';
    user.value = nextUser || null;
    persist();
  };

  const clearSession = () => {
    token.value = '';
    user.value = null;
    persist();
  };

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
