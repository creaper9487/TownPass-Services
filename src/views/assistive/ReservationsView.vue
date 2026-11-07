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
import { centerById, centerShort } from '@/utils/assistive/centers';
import { serviceTitle } from '@/utils/assistive/services';
import type { Reservation } from '@/utils/assistive/types';
import { t, trSummary } from '@/i18n/assistive';
import { useAssistiveNative } from '@/composables/useAssistiveNative';

const native = useAssistiveNative();
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
  const label = removing.value.label;
  try {
    await unsubscribeArrival(removing.value.variantId);
    arrivals.value = listArrivals();
    native.notify('到貨通知已取消', `已取消「${label}」到貨通知`);
  } catch {
    removeFailed.value = true;
  }
};
const centerLine = (r: Reservation) => {
  const c = centerById(r.centerId);
  return t('reservations.centerLine', { center: c ? centerShort(c) : '', id: r.id });
};
const loaded = ref(false);
onMounted(async () => {
  list.value = await listReservations();
  loaded.value = true;
});
</script>

<template>
  <AStepPage :title="t('home.reservations')">
    <ASection grey>
      <p v-if="!loaded" class="text-sm text-grey-700">{{ t('common.loading') }}</p>
      <div
        v-else-if="!list.length && !arrivals.length"
        class="flex flex-col items-center py-10 text-center"
      >
        <img src="@/assets/images/illustrations_no_data.svg" alt="" class="h-32" />
        <p class="mt-4 tp-h3-semibold">{{ t('reservations.empty.title') }}</p>
        <p class="mt-1 text-sm text-grey-700">{{ t('reservations.empty.hint') }}</p>
        <BaseButton class="mt-6 w-full" link :route-info="{ name: 'assistive-home' }">
          {{ t('reservations.empty.cta') }}
        </BaseButton>
      </div>
      <ul v-else-if="list.length" class="flex flex-col gap-3">
        <li v-for="(r, i) in list" :key="r.id" class="a-rise" :style="{ '--i': Math.min(i, 8) }">
          <RouterLink
            :to="{ name: 'assistive-reservation', params: { id: r.id } }"
            class="a11y-focus tp-card flex min-h-20 items-center gap-3 p-4"
          >
            <span class="flex-1">
              <span class="block tp-h3-semibold">{{ serviceTitle(r.service) }}</span>
              <span class="mt-1 block text-sm text-grey-700">
                {{ r.summary.map(trSummary).join(t('reservations.listSep')) || '—' }}
              </span>
              <span class="mt-1 block text-sm text-grey-700">
                {{ centerLine(r) }}
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

    <ASection v-if="loaded && arrivals.length" :title="t('reservations.arrivals')">
      <AErrorText v-if="removeFailed" class="mb-3">
        {{ t('reservations.cancelFailed') }}
      </AErrorText>
      <ul class="flex flex-col gap-3">
        <li
          v-for="a in arrivals"
          :key="a.variantId"
          class="a-rise tp-card flex items-center gap-3 p-4"
        >
          <span class="flex-1">
            <span class="block tp-h3-semibold break-words">{{ a.label }}</span>
            <span class="mt-1 block text-sm text-grey-700">
              {{ t('reservations.registrationNo', { id: a.id }) }}
            </span>
          </span>
          <BaseButton outline @click="askRemove(a)">{{ t('common.cancel') }}</BaseButton>
        </li>
      </ul>
    </ASection>

    <BaseDialog
      v-model="confirming"
      :title="t('reservations.removeDialog.title')"
      :content="removing?.label ?? ''"
      :negative-text="t('reservations.removeDialog.keep')"
      :positive-text="t('reservations.removeDialog.confirm')"
      @on-positive-click="doRemove"
    />
  </AStepPage>
</template>
