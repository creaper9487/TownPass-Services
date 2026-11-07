<script setup lang="ts">
import { computed } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import CenterCard from '@/components/assistive/CenterCard.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { deadlineText, pickupDatesText } from '@/utils/assistive/api';
import { centerById, mapUrl } from '@/utils/assistive/centers';
import { services } from '@/utils/assistive/services';

const store = useAssistiveStore();
const native = useAssistiveNative();
const r = store.submitted!;
const center = computed(() => centerById(r.centerId)!);
const isBorrow = r.service === 'borrow';
const deadline = deadlineText(r);
const dates = pickupDatesText(r);
const pickupSentence = `請在 ${dates} 到中心取貨。取貨期限是 ${deadline}，逾期預約會自動取消。`;
</script>

<template>
  <AStepPage :title="isBorrow ? '預約成功' : '已送出申請'" :lead="services[r.service].title">
    <ASection>
      <div class="flex items-center gap-3 rounded-lg bg-primary-50 p-4">
        <img src="@/assets/images/check-icon-outline.svg" alt="" class="h-10 w-10 shrink-0" />
        <div>
          <p class="text-sm text-grey-700">預約編號</p>
          <p class="tp-h2">{{ r.id }}</p>
        </div>
      </div>
    </ASection>

    <ASection title="接下來">
      <ol class="list-decimal space-y-3 pl-5 text-base">
        <template v-if="isBorrow">
          <li>
            {{ pickupSentence }}
          </li>
          <li>帶使用者或借用人的<strong>身分證正本</strong>，現場填寫借用申請單。</li>
          <li>借期 3 個月，依單據上的日期歸還。</li>
        </template>
        <template v-else>
          <li>
            中心會在開館時間打給你（{{
              r.mobile
            }}），<strong>確認後才算申請完成</strong>，請留意來電。
          </li>
          <li>有急迫需求，可以直接打電話給中心。</li>
        </template>
      </ol>
    </ASection>

    <ASection :title="isBorrow ? '取貨地點' : '辦理中心'">
      <CenterCard :center="center" />
      <div class="mt-3 grid grid-cols-2 gap-2">
        <BaseButton outline @click="native.callPhone(center.phone)">撥打電話</BaseButton>
        <BaseButton outline @click="native.openMap(mapUrl(center))">導航前往</BaseButton>
      </div>
    </ASection>

    <template #footer>
      <div class="grid grid-cols-2 gap-2">
        <BaseButton outline link :route-info="{ name: 'assistive-reservations' }">
          服務預約查詢與取消
        </BaseButton>
        <BaseButton link :route-info="{ name: 'assistive-home' }">回輔具預約</BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
