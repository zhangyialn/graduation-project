/** notify：统一封装消息提示与接口错误解析 */
// 改为组件级按需引入，避免把整个 Element Plus 消息体系打进首包。
import { ElMessage } from 'element-plus/es/components/message/index';
import 'element-plus/es/components/message/style/css';

const baseOptions = {
  showClose: true,
  offset: 20
};

export const notifySuccess = (message, duration = 2200) => {
  if (!message) return;
  ElMessage({
    ...baseOptions,
    type: 'success',
    message,
    duration
  });
};

export const notifyError = (message, duration = 2400) => {
  if (!message) return;
  ElMessage({
    ...baseOptions,
    type: 'error',
    message,
    duration
  });
};

export const notifyWarning = (message, duration = 2000) => {
  if (!message) return;
  ElMessage({
    ...baseOptions,
    type: 'warning',
    message,
    duration
  });
};

export const notifyInfo = (message, duration = 2200) => {
  if (!message) return;
  ElMessage({
    ...baseOptions,
    type: 'info',
    message,
    duration
  });
};

export const resolveApiErrorMessage = (error, fallback = '请求失败') => {
  const data = error?.response?.data;
  const errors = Array.isArray(data?.errors) ? data.errors : [];

  if (errors.length > 0) {
    const details = errors
      .map((item) => {
        if (!item) return '';
        if (typeof item === 'string') return item;
        const field = item.field ? `${item.field}: ` : '';
        const message = item.message || '';
        return `${field}${message}`.trim();
      })
      .filter(Boolean)
      .join('；');

    if (details) {
      return data?.message && !String(data.message).startsWith('参数验证失败')
        ? `${data.message}：${details}`
        : `参数验证失败：${details}`;
    }
  }

  return data?.message || error?.message || fallback;
};
