<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import AErrorText from '@/components/assistive/AErrorText.vue';
import AIcon from '@/components/assistive/AIcon.vue';
import AItemCard from '@/components/assistive/AItemCard.vue';
import { variantInfo } from '@/utils/assistive/catalog';
import ADialog from '@/components/assistive/ADialog.vue';
import {
  effectiveStatus,
  listArrivals,
  loadArrivals,
  listReservations,
  statusText,
  unsubscribeArrival,
  type ArrivalNotice
} from '@/utils/assistive/api';
import { centerById, centerShort } from '@/utils/assistive/centers';
import { serviceTitle } from '@/utils/assistive/services';
import type { Reservation } from '@/utils/assistive/types';
import { t, trSummary } from '@/i18n/assistive';

const list = ref<Reservation[]>([]);
const arrivals = ref<ArrivalNotice[]>(listArrivals());
const removing = ref<ArrivalNotice | null>(null);
const confirming = ref(false);
const removeFailed = ref(false);
// 取消到貨通知是使用者自己剛做的事：用彈窗告知，不發通知
const removedDialog = ref(false);
const removedLabel = ref('');

const askRemove = (a: ArrivalNotice) => {
  removing.value = a;
  removeFailed.value = false;
  confirming.value = true;
};
const doRemove = async () => {
  if (!removing.value) return;
  // 彈窗只寫品名，不用「類別・品名・規格」串成的長字串
  const label = variantInfo(removing.value.variantId)?.name ?? removing.value.label;
  try {
    await unsubscribeArrival(removing.value.variantId);
    arrivals.value = listArrivals();
    removedLabel.value = label;
    removedDialog.value = true;
  } catch {
    removeFailed.value = true;
  }
};
const firstItem = (r: Reservation) => (r.itemIds?.[0] ? variantInfo(r.itemIds[0]) : undefined);
const centerLine = (r: Reservation) => {
  const c = centerById(r.centerId);
  return t('reservations.centerLine', { center: c ? centerShort(c) : '' });
};
const loaded = ref(false);
const sortedArrivals = computed(() =>
  [...arrivals.value].sort(
    (a, b) => Number(b.status === 'arrived') - Number(a.status === 'arrived')
  )
);
onMounted(async () => {
  // 預約與到貨通知各自向後端更新；到貨通知先顯示這台裝置記得的，後端回應後換成最新（含已到貨）
  const [reservations] = await Promise.all([
    listReservations(),
    loadArrivals().then((latest) => (arrivals.value = latest))
  ]);
  list.value = reservations;
  loaded.value = true;
});
</script>

<template>
  <AStepPage :title="t('home.reservations')">
    <!-- 到貨通知是使用者在等的事，放在預約紀錄上面；已到貨的排最前面 -->
    <ASection v-if="loaded && arrivals.length" :title="t('reservations.arrivals')">
      <AErrorText v-if="removeFailed" class="mb-3">
        {{ t('reservations.cancelFailed') }}
      </AErrorText>
      <ul class="flex flex-col gap-3">
        <li
          v-for="a in sortedArrivals"
          :key="a.variantId"
          class="a-rise tp-card flex items-center gap-3 p-4"
        >
          <span class="min-w-0 flex-1">
            <AItemCard v-if="variantInfo(a.variantId)" :item="variantInfo(a.variantId)!" compact />
            <span v-else class="block tp-h3-semibold break-words">{{ a.label }}</span>
            <span class="mt-2 block text-sm text-grey-700">
              {{ t('reservations.registrationNo', { id: a.id }) }}
            </span>
            <span
              class="tp-tag mt-2 inline-flex items-center gap-1"
              :class="{ '!border-grey-300 !text-grey-700': a.status !== 'arrived' }"
            >
              <AIcon
                :name="a.status === 'arrived' ? 'check' : 'hourglass'"
                class="h-[14px] w-[14px] shrink-0"
              />
              {{
                a.status === 'arrived'
                  ? t('reservations.arrivalArrived')
                  : t('reservations.arrivalWaiting')
              }}
            </span>
          </span>
          <div class="flex flex-col gap-2">
            <!-- 直接帶著這件輔具到選中心，不用再從分類找一次 -->
            <BaseButton
              v-if="a.status === 'arrived'"
              link
              :route-info="{
                name: 'assistive-borrow-quick',
                params: { service: 'borrow', variantId: a.variantId }
              }"
            >
              {{ t('reservations.arrivalReserve') }}
            </BaseButton>
            <BaseButton outline @click="askRemove(a)">{{ t('common.cancel') }}</BaseButton>
          </div>
        </li>
      </ul>
    </ASection>
    <ASection
      grey
      :title="loaded && arrivals.length && list.length ? t('reservations.listTitle') : undefined"
    >
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
              <span v-if="firstItem(r)" class="mt-2 block">
                <AItemCard :item="firstItem(r)!" compact />
                <span v-if="(r.itemIds?.length ?? 0) > 1" class="mt-1 block text-sm text-grey-700">
                  {{ t('reservations.moreItems', { n: (r.itemIds?.length ?? 1) - 1 }) }}
                </span>
              </span>
              <span v-else class="mt-1 block text-sm text-grey-700">
                {{ r.summary.map(trSummary).join(t('reservations.listSep')) || '—' }}
              </span>
              <span class="mt-1 block text-sm text-grey-700">{{ centerLine(r) }}</span>
              <span class="block text-sm text-grey-700">
                {{ t('reservations.number') }} {{ r.id }}
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

    <ADialog
      v-model="removedDialog"
      is-check
      :title="t('reservations.removedDialog.title')"
      :content="t('reservations.removedDialog.content', { label: trSummary(removedLabel) })"
    />
    <ADialog
      v-model="confirming"
      :title="t('reservations.removeDialog.title')"
      :negative-text="t('reservations.removeDialog.keep')"
      :positive-text="t('reservations.removeDialog.confirm')"
      @on-positive-click="doRemove"
    >
      <template #content>
        <AItemCard
          v-if="removing && variantInfo(removing.variantId)"
          :item="variantInfo(removing.variantId)!"
        />
        <p v-else class="text-center text-base">{{ removing?.label }}</p>
      </template>
    </ADialog>
  </AStepPage>
</template>
