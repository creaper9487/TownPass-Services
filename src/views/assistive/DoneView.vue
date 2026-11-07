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
import { serviceTitle } from '@/utils/assistive/services';
import { t } from '@/i18n/assistive';

const store = useAssistiveStore();
const native = useAssistiveNative();
const r = store.submitted!;
const center = computed(() => centerById(r.centerId)!);
const isBorrow = r.service === 'borrow';
const pickupSentence = computed(() =>
  t('done.pickup', { dates: pickupDatesText(r), deadline: deadlineText(r) })
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
      <ol class="list-decimal space-y-3 pl-5 text-base">
        <template v-if="isBorrow">
          <li>
            {{ pickupSentence }}
          </li>
          <li>
            <span>{{ t('done.id.before') }}</span>
            <strong>{{ t('done.id.bold') }}</strong>
            <span>{{ t('done.id.after') }}</span>
          </li>
          <li>{{ t('done.loan') }}</li>
        </template>
        <template v-else>
          <li>
            <span>{{ t('done.call.before', { mobile: r.mobile }) }}</span>
            <strong>{{ t('done.call.bold') }}</strong>
            <span>{{ t('done.call.after') }}</span>
          </li>
          <li>{{ t('done.urgent') }}</li>
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
