<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { effectiveStatus, listReservations, statusText } from '@/utils/assistive/api';
import { centerById } from '@/utils/assistive/centers';
import { services } from '@/utils/assistive/services';
import type { Reservation } from '@/utils/assistive/types';

const list = ref<Reservation[]>([]);
const loaded = ref(false);
onMounted(async () => {
  list.value = await listReservations();
  loaded.value = true;
});
</script>

<template>
  <AStepPage title="我的預約">
    <ASection grey>
      <p v-if="!loaded" class="text-sm text-grey-700">讀取中…</p>
      <div v-else-if="!list.length" class="flex flex-col items-center py-10 text-center">
        <img src="@/assets/images/illustrations_no_data.svg" alt="" class="h-32" />
        <p class="mt-4 tp-h3-semibold">目前沒有預約紀錄</p>
        <p class="mt-1 text-sm text-grey-700">預約過的輔具服務會顯示在這裡。</p>
        <BaseButton class="mt-6 w-full" link :route-info="{ name: 'assistive-home' }">
          去預約
        </BaseButton>
      </div>
      <ul v-else class="flex flex-col gap-3">
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
  </AStepPage>
</template>
