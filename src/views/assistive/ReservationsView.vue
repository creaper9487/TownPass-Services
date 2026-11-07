<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import AErrorText from '@/components/assistive/AErrorText.vue';
import BaseDialog from '@/components/atoms/BaseDialog.vue';
import {
  effectiveStatus,
  listArrivals,
  listReservations,
  statusText,
  unsubscribeArrival,
  type ArrivalNotice
} from '@/utils/assistive/api';
import { centerById } from '@/utils/assistive/centers';
import { services } from '@/utils/assistive/services';
import type { Reservation } from '@/utils/assistive/types';

const list = ref<Reservation[]>([]);
const arrivals = ref<ArrivalNotice[]>(listArrivals());
const removing = ref<ArrivalNotice | null>(null);
const confirming = ref(false);
const removeFailed = ref(false);

const askRemove = (a: ArrivalNotice) => {
  removing.value = a;
  removeFailed.value = false;
  confirming.value = true;
};
const doRemove = async () => {
  if (!removing.value) return;
  try {
    await unsubscribeArrival(removing.value.variantId);
    arrivals.value = listArrivals();
  } catch {
    removeFailed.value = true;
  }
};
const loaded = ref(false);
onMounted(async () => {
  list.value = await listReservations();
  loaded.value = true;
});
</script>

<template>
  <AStepPage title="服務預約查詢與取消">
    <ASection grey>
      <p v-if="!loaded" class="text-sm text-grey-700">讀取中…</p>
      <div
        v-else-if="!list.length && !arrivals.length"
        class="flex flex-col items-center py-10 text-center"
      >
        <img src="@/assets/images/illustrations_no_data.svg" alt="" class="h-32" />
        <p class="mt-4 tp-h3-semibold">目前沒有預約紀錄</p>
        <p class="mt-1 text-sm text-grey-700">預約過的輔具服務會顯示在這裡。</p>
        <BaseButton class="mt-6 w-full" link :route-info="{ name: 'assistive-home' }">
          去預約
        </BaseButton>
      </div>
      <ul v-else-if="list.length" class="flex flex-col gap-3">
        <li v-for="r in list" :key="r.id">
          <RouterLink
            :to="{ name: 'assistive-reservation', params: { id: r.id } }"
            class="a11y-focus tp-card flex min-h-20 items-center gap-3 p-4"
          >
            <span class="flex-1">
              <span class="block tp-h3-semibold">{{ services[r.service].title }}</span>
              <span class="mt-1 block text-sm text-grey-700">
                {{ r.summary.join('、') || '—' }}
              </span>
              <span class="mt-1 block text-sm text-grey-700">
                {{ centerById(r.centerId)?.shortName }}輔具中心 {{ r.id }}
              </span>
              <span
                class="tp-tag mt-2"
                :class="{
                  '!border-grey-300 !text-grey-700': ['cancelled', 'expired'].includes(
                    effectiveStatus(r)
                  )
                }"
              >
                {{ statusText(r) }}
              </span>
            </span>
            <img src="@/assets/images/down-icon.svg" alt="" class="h-6 w-6 -rotate-90" />
          </RouterLink>
        </li>
      </ul>
    </ASection>

    <ASection v-if="loaded && arrivals.length" title="到貨通知">
      <AErrorText v-if="removeFailed" class="mb-3">取消失敗，請檢查網路後再試一次。</AErrorText>
      <ul class="flex flex-col gap-3">
        <li v-for="a in arrivals" :key="a.variantId" class="tp-card flex items-center gap-3 p-4">
          <span class="flex-1">
            <span class="block tp-h3-semibold break-words">{{ a.label }}</span>
            <span class="mt-1 block text-sm text-grey-700">登記編號 {{ a.id }}</span>
          </span>
          <BaseButton outline @click="askRemove(a)">取消</BaseButton>
        </li>
      </ul>
    </ASection>

    <BaseDialog
      v-model="confirming"
      title="要取消到貨通知嗎？"
      :content="removing?.label ?? ''"
      negative-text="先不要"
      positive-text="取消通知"
      @on-positive-click="doRemove"
    />
  </AStepPage>
</template>
