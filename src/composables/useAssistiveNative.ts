import { useConnectionMessage } from '@/composables/useConnectionMessage';

/**
 * 台北通 App 提供的原生能力；在一般瀏覽器開發時自動退回網頁行為。
 * 訊息名稱對應 TownPass 的 tp_web_message_handler：
 * userinfo / location / phone_call / launch_map / open_link / notify。
 */
export const inApp = () =>
  typeof (window as unknown as { flutterObject?: unknown }).flutterObject !== 'undefined';

export const useAssistiveNative = () => {
  const requestUserInfo = () => useConnectionMessage('userinfo', null);
  const requestLocation = () => useConnectionMessage('location', null);

  const callPhone = (phone: string) => {
    const digits = phone.replace(/\D/g, '');
    if (inApp()) useConnectionMessage('phone_call', digits);
    else window.location.href = `tel:${digits}`;
  };

  const openMap = (url: string) => {
    if (inApp()) useConnectionMessage('launch_map', url);
    else window.open(url, '_blank', 'noopener');
  };

  const openLink = (url: string) => {
    if (inApp()) useConnectionMessage('open_link', url);
    else window.open(url, '_blank', 'noopener');
  };

  /** 在 App 內跳出系統通知；一般瀏覽器沒有對應能力，直接略過 */
  const notify = (title: string, content: string) => {
    if (inApp()) useConnectionMessage('notify', { title, content });
  };

  return { requestUserInfo, requestLocation, callPhone, openMap, openLink, notify };
};
