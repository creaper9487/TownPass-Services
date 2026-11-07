<script setup lang="ts">
import { ref } from 'vue';
import { RouterView, useRoute, useRouter } from 'vue-router';
import { useHandleConnectionData } from '@/composables/useHandleConnectionData';
import { useAssistiveNative, inApp } from '@/composables/useAssistiveNative';
import { useAssistiveStore } from '@/stores/assistive';
import { installMotion } from '@/composables/useAssistiveMotion';
import { applyLang } from '@/i18n/assistive';
import { ensurePush } from '@/utils/assistive/push';
import { loadCatalog } from '@/utils/assistive/catalog';
import RulesView from './RulesView.vue';

const store = useAssistiveStore();
const route = useRoute();
installMotion(useRouter());
const native = useAssistiveNative();
// Flutter App 已把個資聲明與借用須知合併；一般瀏覽器仍用網頁須知作預覽。
const rulesAccepted = ref(inApp());
// Demo：瀏覽器每次重新開啟服務都重新閱讀。
const agreeToRules = () => { rulesAccepted.value = true; };

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
    if (result.name === 'userinfo') {
      if (data && !Array.isArray(data) && typeof data === 'object') store.setAccount(data);
      else store.account = null;
    }
  } catch {
    /* 非 JSON 訊息，略過 */
  }
});

native.requestUserInfo();

// 目錄（分類、款式、款式代碼）以後端為準；連不上時用隨附的官網快照。
loadCatalog();

// 已經同意推播的話，進入服務時悄悄更新登記（token 換了、使用者撤回授權都會在這裡同步），不會跳視窗。
ensurePush({ silent: true });

// 載入時讓 <html lang> 與網頁標題對上目前的語言。
applyLang();

// 本機開發時沒有 App 可以回傳帳號資料：加上 ?mockUser=1 即可模擬帶入。
if (import.meta.env.DEV && !inApp() && route.query.mockUser) {
  store.setAccount({
    id: `dev-preview-user-${String(route.query.mockUser)}`,
    realName: '王小明',
    phoneNo: '0912345678',
    email: 'xiaoming@example.com',
    idNo: 'A123456789',
    residentAddress: '臺北市信義區市府路1號'
  });
}
</script>

<template>
  <RulesView v-if="!rulesAccepted" @agree="agreeToRules" />
  <RouterView v-else />
</template>
