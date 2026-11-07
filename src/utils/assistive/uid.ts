let seed = 0;
/** Vue 3.4 還沒有 useId，用計數器產生穩定的 label / aria 關聯 id */
export const uid = (prefix = 'a') => `${prefix}-${++seed}`;
