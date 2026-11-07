<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import CenterCard from '@/components/assistive/CenterCard.vue';
import ClosureNotice from '@/components/assistive/ClosureNotice.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { useAssistiveLocate } from '@/composables/useAssistiveLocate';
import { listReservations } from '@/utils/assistive/api';
import { mapUrl } from '@/utils/assistive/centers';
import { serviceOrder, services } from '@/utils/assistive/services';

const store = useAssistiveStore();
const native = useAssistiveNative();
const { locate, locating, message } = useAssistiveLocate();

const activeCount = ref(0);
onMounted(async () => {
  store.loadCalendars();
  activeCount.value = (await listReservations()).filter((r) => r.status !== 'cancelled').length;
});

const VISIT_URL = 'https://tpap.gov.taipei/app37/rentView/rentvisit';
</script>

<template>
  <AStepPage
    title="輔具預約"
    lead="借用、評估、維修與回收都可以在這裡預約。經你同意，台北通資料可以幫你預先填好表單。"
  >
    <ASection v-if="store.closureNotices.length">
      <ClosureNotice :items="store.closureNotices" />
    </ASection>
    <ASection title="你需要什麼協助？" grey>
      <ul class="flex flex-col gap-3">
        <li v-for="id in serviceOrder" :key="id">
          <RouterLink
            :to="{ name: 'assistive-qualify', params: { service: id } }"
            class="a11y-focus tp-card flex min-h-20 items-center gap-3 p-4"
            @click="store.begin(id)"
          >
            <span class="flex-1">
              <span class="block tp-h3-semibold">{{ services[id].title }}</span>
              <span class="mt-1 block text-sm text-grey-700">{{ services[id].situation }}</span>
            </span>
            <img src="@/assets/images/down-icon.svg" alt="" class="h-6 w-6 -rotate-90" />
          </RouterLink>
        </li>
      </ul>
    </ASection>

    <ASection title="離你最近的輔具中心">
      <template v-if="store.recommendedCenter">
        <CenterCard
          :center="store.recommendedCenter"
          :badge="
            store.recommendedBy === 'location'
              ? '離你最近'
              : `符合你的地址（${store.homeDistrict}）`
          "
        />
        <div class="mt-3 grid grid-cols-2 gap-2">
          <BaseButton outline @click="native.callPhone(store.recommendedCenter.phone)">
            撥打電話
          </BaseButton>
          <BaseButton outline @click="native.openMap(mapUrl(store.recommendedCenter))">
            導航前往
          </BaseButton>
        </div>
        <button
          v-if="store.recommendedBy === 'address'"
          type="button"
          class="a11y-focus mt-3 min-h-11 text-base font-semibold text-primary-700 underline"
          :aria-busy="locating"
          @click="locate"
        >
          改用目前位置推薦
        </button>
      </template>
      <template v-else>
        <p class="text-sm text-grey-700">
          三家中心依行政區分工服務。開啟定位後，會推薦離你最近的一家。
        </p>
        <BaseButton class="mt-3 w-full" :aria-busy="locating" @click="locate">
          使用目前位置
        </BaseButton>
      </template>
      <p v-if="message" role="status" class="mt-2 text-sm text-grey-700">{{ message }}</p>
    </ASection>

    <ASection>
      <ul class="-my-2 divide-y divide-grey-100">
        <li>
          <RouterLink
            :to="{ name: 'assistive-reservations' }"
            class="a11y-focus flex min-h-14 items-center justify-between py-2 text-base"
          >
            <span class="font-semibold">我的預約</span>
            <span class="flex items-center gap-2 text-grey-700">
              <span v-if="activeCount">{{ activeCount }} 筆進行中</span>
              <img src="@/assets/images/down-icon.svg" alt="" class="h-6 w-6 -rotate-90" />
            </span>
          </RouterLink>
        </li>
        <li>
          <RouterLink
            :to="{ name: 'assistive-faq' }"
            class="a11y-focus flex min-h-14 items-center justify-between py-2 text-base"
          >
            <span>
              <span class="block font-semibold">常見問題</span>
              <span class="block text-sm text-grey-700">借用、候補、取消、庫存怎麼運作</span>
            </span>
            <img src="@/assets/images/down-icon.svg" alt="" class="h-6 w-6 -rotate-90" />
          </RouterLink>
        </li>
        <li>
          <button
            type="button"
            class="a11y-focus flex min-h-14 w-full items-center justify-between py-2 text-left text-base"
            @click="native.openLink(VISIT_URL)"
          >
            <span>
              <span class="block font-semibold">輔具中心團體參訪</span>
              <span class="block text-sm text-grey-700">於官方網站預約，會另開網頁</span>
            </span>
            <img src="@/assets/images/down-icon.svg" alt="" class="h-6 w-6 -rotate-90" />
          </button>
        </li>
      </ul>
    </ASection>
  </AStepPage>
</template>
