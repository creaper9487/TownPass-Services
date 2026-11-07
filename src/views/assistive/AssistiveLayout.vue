<script setup lang="ts">
import { RouterView, useRoute, useRouter } from 'vue-router';
import { useHandleConnectionData } from '@/composables/useHandleConnectionData';
import { useAssistiveNative, inApp } from '@/composables/useAssistiveNative';
import { useAssistiveStore } from '@/stores/assistive';
import { installMotion } from '@/composables/useAssistiveMotion';
import { applyLang } from '@/i18n/assistive';

const store = useAssistiveStore();
const route = useRoute();
installMotion(useRouter());
const native = useAssistiveNative();

// 整個輔具預約流程只在這裡聽 App 的回覆（userinfo、location），各頁從 store 取用。
// 個資授權由台北通 App 負責詢問：使用者沒有同意時，App 會回傳空值，這裡就當作沒有資料。
useHandleConnectionData((event) => {
  try {
    const result = JSON.parse(event.data);
    const data = result?.data;
    if (result?.name === 'location') {
      if (data && !Array.isArray(data) && typeof data.latitude === 'number') {
        store.location = { lat: data.latitude, lng: data.longitude };
      } else {
        store.locationFailures++;
      }
      return;
    }
    if (!data || Array.isArray(data)) return;
    if (result.name === 'userinfo') store.setAccount(data);
  } catch {
    /* 非 JSON 訊息，略過 */
  }
});

native.requestUserInfo();

// 載入時讓 <html lang> 與網頁標題對上目前的語言。
applyLang();

// 本機開發時沒有 App 可以回傳帳號資料：加上 ?mockUser=1 即可模擬帶入。
if (import.meta.env.DEV && !inApp() && route.query.mockUser) {
  store.setAccount({
    realName: '王小明',
    phoneNo: '0912345678',
    email: 'xiaoming@example.com',
    idNo: 'A123456789',
    residentAddress: '臺北市信義區市府路1號'
  });
}
</script>

<template>
  <RouterView />
</template>
