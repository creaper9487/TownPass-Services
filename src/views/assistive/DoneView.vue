<script setup lang="ts">
import { computed } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import CenterCard from '@/components/assistive/CenterCard.vue';
import AInfoRow from '@/components/assistive/AInfoRow.vue';
import APickupDays from '@/components/assistive/APickupDays.vue';
import APickupCountdown from '@/components/assistive/APickupCountdown.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { deadlineText, pickupDatesText } from '@/utils/assistive/api';
import { centerById, mapUrl } from '@/utils/assistive/centers';
import { serviceTitle } from '@/utils/assistive/services';
import { pickupDays, pickupRemaining } from '@/utils/assistive/pickup';
import { useTaipeiNow } from '@/utils/assistive/time';
import { t } from '@/i18n/assistive';

const store = useAssistiveStore();
const native = useAssistiveNative();
const r = store.submitted!;
const center = computed(() => centerById(r.centerId)!);
const isBorrow = r.service === 'borrow';
const now = useTaipeiNow();
const days = computed(() => pickupDays(r, now.value));
const remaining = computed(() => pickupRemaining(r, now.value));
// 期限內沒有開館日時沒有「可以去的日子」可列，句子改成只講期限，不要留下「請在 到中心取貨」這種空洞的句子。
const pickupSentence = computed(() =>
  r.pickupDates?.length
    ? t('done.pickup', { dates: pickupDatesText(r), deadline: deadlineText(r) })
    : t('done.pickupNoDates', { deadline: deadlineText(r) })
);
</script>

<template>
  <AStepPage
    :title="isBorrow ? t('done.titleBorrow') : t('done.titleAssess')"
    :lead="serviceTitle(r.service)"
  >
    <ASection>
      <div class="flex items-center gap-3 rounded-lg bg-primary-50 p-4">
        <img src="@/assets/images/check-icon-outline.svg" alt="" class="a-pop h-10 w-10 shrink-0" />
        <div>
          <p class="text-sm text-grey-700">{{ t('reservations.number') }}</p>
          <p class="tp-h2">{{ r.id }}</p>
        </div>
      </div>
    </ASection>

    <ASection :title="t('done.next')">
      <ol role="list" class="flex flex-col gap-5">
        <template v-if="isBorrow">
          <AInfoRow icon="calendar">
            <p>{{ pickupSentence }}</p>
            <div v-if="days.length || remaining" class="mt-3 flex flex-col items-start gap-3">
              <APickupCountdown v-if="remaining" :remaining="remaining" />
              <APickupDays v-if="days.length" :days="days" class="w-full" />
            </div>
          </AInfoRow>
          <AInfoRow icon="idcard">
            <span>{{ t('done.id.before') }}</span>
            <strong>{{ t('done.id.bold') }}</strong>
            <span>{{ t('done.id.after') }}</span>
          </AInfoRow>
          <AInfoRow icon="refresh">{{ t('done.loan') }}</AInfoRow>
        </template>
        <template v-else>
          <AInfoRow icon="phone">
            <strong>{{ t('done.call.bold') }}</strong>
            <span>{{ t('done.call.after', { mobile: r.mobile }) }}</span>
          </AInfoRow>
          <AInfoRow icon="alert">{{ t('done.urgent') }}</AInfoRow>
        </template>
      </ol>
    </ASection>

    <ASection :title="isBorrow ? t('done.pickupPlace') : t('done.center')">
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

    <template #footer>
      <div class="grid grid-cols-2 gap-2">
        <BaseButton outline link :route-info="{ name: 'assistive-reservations' }">
          {{ t('home.reservations') }}
        </BaseButton>
        <BaseButton link :route-info="{ name: 'assistive-home' }">{{ t('done.back') }}</BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
