import { ElMessage } from 'element-plus';

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
