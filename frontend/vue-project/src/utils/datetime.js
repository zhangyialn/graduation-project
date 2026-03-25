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

const parseDateLike = (value) => {
  if (!value) return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  const text = String(value).trim();
  if (!text) return null;
  const hasTimezone = /([zZ]|[+-]\d{2}:\d{2})$/.test(text);
  const parsed = new Date(hasTimezone ? text : `${text}Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

export const formatBeijingDateTime = (value) => {
  const parsed = parseDateLike(value);
  if (!parsed) return '-';
  return beijingFormatter.format(parsed);
};

export const getBeijingDateKey = (value = new Date()) => {
  const parsed = parseDateLike(value) || new Date();
  return beijingDateKeyFormatter.format(parsed);
};

export const getBeijingHour = (value = new Date()) => {
  const parsed = parseDateLike(value) || new Date();
  return Number(beijingHourFormatter.format(parsed));
};
