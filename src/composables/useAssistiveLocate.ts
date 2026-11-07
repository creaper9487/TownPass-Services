import { onBeforeUnmount, ref, watch } from 'vue';
import { useAssistiveStore } from '@/stores/assistive';
import { inApp, useAssistiveNative } from './useAssistiveNative';

/**
 * 「使用目前位置」：App 內走原生 location，一般瀏覽器走 navigator.geolocation。
 * 只在使用者按下按鈕時才要位置，不會一進頁面就跳出權限詢問。
 */
export const useAssistiveLocate = () => {
  const store = useAssistiveStore();
  const native = useAssistiveNative();
  const locating = ref(false);
  const message = ref('');
  let timer: ReturnType<typeof setTimeout> | undefined;

  const fail = (text = '無法取得位置，請確認已開啟定位權限，或改用地址推薦。') => {
    locating.value = false;
    message.value = text;
  };

  const locate = () => {
    locating.value = true;
    message.value = '正在取得位置…';
    clearTimeout(timer);

    if (inApp()) {
      native.requestLocation();
      timer = setTimeout(() => locating.value && fail(), 8000);
      return;
    }
    if (!navigator.geolocation) return fail('這個裝置不支援定位。');
    navigator.geolocation.getCurrentPosition(
      (p) => {
        store.location = { lat: p.coords.latitude, lng: p.coords.longitude };
      },
      () => fail(),
      { timeout: 10000, maximumAge: 300000 }
    );
  };

  // 位置到了就算成功；即使先前有一次失敗的回覆（例如權限視窗還沒按完），也以最終結果為準。
  watch(
    () => store.location,
    (loc) => {
      if (loc) {
        locating.value = false;
        clearTimeout(timer);
        message.value = '已依你目前的位置排序。';
      }
    }
  );
  // App 回報取不到位置時，稍等一下再顯示失敗，避免跟隨後才到的成功結果互相打架。
  watch(
    () => store.locationFailures,
    () => {
      setTimeout(() => {
        if (locating.value && !store.location) {
          fail(
            '沒有取得位置。請確認已在「歷程與授權管理」授權、手機定位也有開啟，或改用地址推薦。'
          );
        }
      }, 2500);
    }
  );
  onBeforeUnmount(() => clearTimeout(timer));

  return { locate, locating, message };
};
