<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import CenterCard from '@/components/assistive/CenterCard.vue';
import AStatusSteps from '@/components/assistive/AStatusSteps.vue';
import APickupCountdown from '@/components/assistive/APickupCountdown.vue';
import AErrorText from '@/components/assistive/AErrorText.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import BaseDialog from '@/components/atoms/BaseDialog.vue';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { isPushRegistered } from '@/utils/assistive/push';
import { pickupRemaining } from '@/utils/assistive/pickup';
import { useTaipeiNow } from '@/utils/assistive/time';
import {
  cancelReservation,
  deadlineText,
  listReservations,
  pickupDatesText,
  effectiveStatus,
  statusText
} from '@/utils/assistive/api';
import { centerById, mapUrl } from '@/utils/assistive/centers';
import { serviceTitle } from '@/utils/assistive/services';
import type { Reservation } from '@/utils/assistive/types';
import { t, trSummary } from '@/i18n/assistive';

const route = useRoute();
const native = useAssistiveNative();

const now = useTaipeiNow();
const reservation = ref<Reservation>();
const remaining = computed(() =>
  reservation.value ? pickupRemaining(reservation.value, now.value) : null
);
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
    const id = reservation.value.id;
    await cancelReservation(id);
    reservation.value = { ...reservation.value, status: 'cancelled' };
    // 已登記推播時，後端會推播「預約已取消」，不再跳同一則本機通知。
    if (!isPushRegistered()) native.notify('輔具預約已取消', `預約編號 ${id} 已成功取消。`);
  } catch {
    cancelFailed.value = true;
  } finally {
    cancelling.value = false;
  }
};
</script>

<template>
  <AStepPage
    :title="reservation ? serviceTitle(reservation.service) : t('reservations.detailTitle')"
  >
    <ASection v-if="!loaded">
      <p class="text-sm text-grey-700">{{ t('common.loading') }}</p>
    </ASection>
    <ASection v-else-if="!reservation">
      <p class="tp-h3-semibold">{{ t('reservations.notFound') }}</p>
      <BaseButton class="mt-4 w-full" link :route-info="{ name: 'assistive-reservations' }">
        {{ t('reservations.backToList') }}
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
        <AStatusSteps
          class="mt-4"
          :status="effectiveStatus(reservation)"
          :service="reservation.service"
        />
        <APickupCountdown v-if="remaining" :remaining="remaining" class="mt-4" />
        <dl class="mt-4 divide-y divide-grey-100">
          <div class="grid grid-cols-[5rem_1fr] gap-3 py-3 text-base first:pt-0">
            <dt class="text-grey-700">{{ t('reservations.number') }}</dt>
            <dd>{{ reservation.id }}</dd>
          </div>
          <div class="grid grid-cols-[5rem_1fr] gap-3 py-3 text-base">
            <dt class="text-grey-700">{{ t('reservations.row.item') }}</dt>
            <dd class="whitespace-pre-line">{{ reservation.summary.map(trSummary).join('\n') }}</dd>
          </div>
          <div
            v-if="
              reservation.pickupDeadline &&
              ['booked', 'submitted', 'confirmed'].includes(effectiveStatus(reservation))
            "
            class="grid grid-cols-[5rem_1fr] gap-3 py-3 text-base"
          >
            <dt class="text-grey-700">{{ t('reservations.row.pickup') }}</dt>
            <dd>
              {{ t('reservations.pickupBy', { date: deadlineText(reservation) })
              }}<span v-if="reservation.pickupDates?.length" class="block text-sm text-grey-700">
                {{ t('reservations.visitOn', { dates: pickupDatesText(reservation) }) }}
              </span>
            </dd>
          </div>
          <div class="grid grid-cols-[5rem_1fr] gap-3 py-3 text-base">
            <dt class="text-grey-700">{{ t('reservations.row.contact') }}</dt>
            <dd>{{ reservation.contactName }} {{ reservation.mobile }}</dd>
          </div>
        </dl>
      </ASection>
      <ASection v-if="center" :title="t('reservations.center')">
        <CenterCard :center="center" />
        <div class="mt-3 grid grid-cols-2 gap-2">
          <BaseButton outline @click="native.callPhone(center.phone)">
            {{ t('common.call') }}
          </BaseButton>
          <BaseButton outline @click="native.openMap(mapUrl(center))">
            {{ t('common.navigate') }}
          </BaseButton>
        </div>
      </ASection>
    </template>

    <template v-if="canCancel" #footer>
      <AErrorText v-if="cancelFailed" class="mb-2">{{ t('reservations.cancelFailed') }}</AErrorText>
      <BaseButton outline class="w-full !py-4" :aria-busy="cancelling" @click="confirming = true">
        {{ t('reservations.cancel') }}
      </BaseButton>
    </template>

    <BaseDialog
      v-model="confirming"
      :title="t('reservations.cancelDialog.title')"
      :content="t('reservations.cancelDialog.content')"
      :negative-text="t('reservations.cancelDialog.keep')"
      :positive-text="t('reservations.cancelDialog.confirm')"
      @on-positive-click="doCancel"
    />
  </AStepPage>
</template>
