<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import CenterCard from '@/components/assistive/CenterCard.vue';
import AErrorText from '@/components/assistive/AErrorText.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import BaseDialog from '@/components/atoms/BaseDialog.vue';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import {
  cancelReservation,
  deadlineText,
  listReservations,
  pickupDatesText,
  effectiveStatus,
  statusText
} from '@/utils/assistive/api';
import { centerById, mapUrl } from '@/utils/assistive/centers';
import { services } from '@/utils/assistive/services';
import type { Reservation } from '@/utils/assistive/types';

const route = useRoute();
const native = useAssistiveNative();

const reservation = ref<Reservation>();
const loaded = ref(false);
const confirming = ref(false);
const cancelling = ref(false);
const cancelFailed = ref(false);

const center = computed(() =>
  reservation.value ? centerById(reservation.value.centerId) : undefined
);
const canCancel = computed(
  () =>
    reservation.value &&
    ['booked', 'submitted', 'confirmed'].includes(effectiveStatus(reservation.value))
);

const load = async () => {
  loaded.value = false;
  reservation.value = (await listReservations()).find((r) => r.id === route.params.id);
  loaded.value = true;
};
onMounted(load);
// 同一個頁面元件在兩筆預約之間切換時不會重新建立，要自己重新載入。
watch(() => route.params.id, load);

const doCancel = async () => {
  if (!reservation.value) return;
  cancelling.value = true;
  cancelFailed.value = false;
  try {
    await cancelReservation(reservation.value.id);
    reservation.value = { ...reservation.value, status: 'cancelled' };
  } catch {
    cancelFailed.value = true;
  } finally {
    cancelling.value = false;
  }
};
</script>

<template>
  <AStepPage :title="reservation ? services[reservation.service].title : '預約明細'">
    <ASection v-if="!loaded">
      <p class="text-sm text-grey-700">讀取中…</p>
    </ASection>
    <ASection v-else-if="!reservation">
      <p class="tp-h3-semibold">找不到這筆預約</p>
      <BaseButton class="mt-4 w-full" link :route-info="{ name: 'assistive-reservations' }">
        回服務預約查詢與取消
      </BaseButton>
    </ASection>
    <template v-else>
      <ASection>
        <p
          role="status"
          class="tp-tag"
          :class="{
            '!border-grey-300 !text-grey-700': ['cancelled', 'expired'].includes(
              effectiveStatus(reservation)
            )
          }"
        >
          {{ statusText(reservation) }}
        </p>
        <dl class="mt-3 divide-y divide-grey-100">
          <div class="grid grid-cols-[5rem_1fr] gap-3 py-3 text-base first:pt-0">
            <dt class="text-grey-700">預約編號</dt>
            <dd>{{ reservation.id }}</dd>
          </div>
          <div class="grid grid-cols-[5rem_1fr] gap-3 py-3 text-base">
            <dt class="text-grey-700">項目</dt>
            <dd class="whitespace-pre-line">{{ reservation.summary.join('\n') }}</dd>
          </div>
          <div
            v-if="
              reservation.pickupDeadline &&
              ['booked', 'submitted', 'confirmed'].includes(effectiveStatus(reservation))
            "
            class="grid grid-cols-[5rem_1fr] gap-3 py-3 text-base"
          >
            <dt class="text-grey-700">取貨期限</dt>
            <dd>
              {{ deadlineText(reservation) }}前<span
                v-if="reservation.pickupDates?.length"
                class="block text-sm text-grey-700"
              >
                可前往：{{ pickupDatesText(reservation) }}
              </span>
            </dd>
          </div>
          <div class="grid grid-cols-[5rem_1fr] gap-3 py-3 text-base">
            <dt class="text-grey-700">聯絡人</dt>
            <dd>{{ reservation.contactName }} {{ reservation.mobile }}</dd>
          </div>
        </dl>
      </ASection>
      <ASection v-if="center" title="辦理中心">
        <CenterCard :center="center" />
        <div class="mt-3 grid grid-cols-2 gap-2">
          <BaseButton outline @click="native.callPhone(center.phone)">撥打電話</BaseButton>
          <BaseButton outline @click="native.openMap(mapUrl(center))">導航前往</BaseButton>
        </div>
      </ASection>
    </template>

    <template v-if="canCancel" #footer>
      <AErrorText v-if="cancelFailed" class="mb-2">取消失敗，請檢查網路後再試一次。</AErrorText>
      <BaseButton outline class="w-full !py-4" :aria-busy="cancelling" @click="confirming = true">
        取消這筆預約
      </BaseButton>
    </template>

    <BaseDialog
      v-model="confirming"
      title="要取消這筆預約嗎？"
      content="取消後庫存會釋出給其他人，需要時得重新預約。"
      negative-text="先不要"
      positive-text="取消預約"
      @on-positive-click="doCancel"
    />
  </AStepPage>
</template>
