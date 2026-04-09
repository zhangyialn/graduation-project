/**
 * 日期时间工具：前端统一按北京时间展示，避免浏览器本地时区导致的时间偏差。
 */
const BEIJING_TIMEZONE = 'Asia/Shanghai';

const beijingFormatter = new Intl.DateTimeFormat('zh-CN', {
  timeZone: BEIJING_TIMEZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false
});

const beijingDateKeyFormatter = new Intl.DateTimeFormat('en-CA', {
  timeZone: BEIJING_TIMEZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit'
});

const beijingHourFormatter = new Intl.DateTimeFormat('en-US', {
  timeZone: BEIJING_TIMEZONE,
  hour: '2-digit',
  hour12: false
});

// 兼容 Date/字符串输入，统一转成可用 Date 对象；无效值返回 null。
const parseDateLike = (value) => {
  if (!value) return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  const text = String(value).trim();
  if (!text) return null;
  // 兼容后端返回“无时区字符串”的场景：默认按 UTC 解析后再格式化为北京时间。
  const hasTimezone = /([zZ]|[+-]\d{2}:\d{2})$/.test(text);
  const parsed = new Date(hasTimezone ? text : `${text}Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

// 用于列表、详情页的统一时间展示。
export const formatBeijingDateTime = (value) => {
  const parsed = parseDateLike(value);
  if (!parsed) return '-';
  return beijingFormatter.format(parsed);
};

// 生成“YYYY-MM-DD”日期键，供油价缓存与按日查询使用。
export const getBeijingDateKey = (value = new Date()) => {
  const parsed = parseDateLike(value) || new Date();
  return beijingDateKeyFormatter.format(parsed);
};

// 获取北京时间小时数，用于首页问候语等文案判断。
export const getBeijingHour = (value = new Date()) => {
  const parsed = parseDateLike(value) || new Date();
  return Number(beijingHourFormatter.format(parsed));
};
