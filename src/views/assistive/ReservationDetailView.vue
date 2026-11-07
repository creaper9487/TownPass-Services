<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import CenterCard from '@/components/assistive/CenterCard.vue';
import AStatusSteps from '@/components/assistive/AStatusSteps.vue';
import AItemCard from '@/components/assistive/AItemCard.vue';
import { variantInfo, type VariantInfo } from '@/utils/assistive/catalog';
import APickupCountdown from '@/components/assistive/APickupCountdown.vue';
import AErrorText from '@/components/assistive/AErrorText.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import ADialog from '@/components/assistive/ADialog.vue';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
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
const cancelledDialog = ref(false);
const cancelFailed = ref(false);

const center = computed(() =>
  reservation.value ? centerById(reservation.value.centerId) : undefined
);
// 借用的項目用照片＋品名＋規格顯示；舊紀錄沒有款式代碼、或目錄裡找不到時退回文字
const itemInfos = computed<VariantInfo[]>(() =>
  (reservation.value?.itemIds ?? []).flatMap((id) => variantInfo(id) ?? [])
);
const needsVisit = computed(
  () => reservation.value?.service === 'borrow' && effectiveStatus(reservation.value) === 'booked'
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
    // 取消是使用者自己剛做的事，用彈窗告知就好，不發通知。
    cancelledDialog.value = true;
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
        <dl class="a-dl mt-4 divide-y divide-grey-100">
          <div class="a-dl-row py-3 text-base first:pt-0">
            <dt class="text-grey-700">{{ t('reservations.number') }}</dt>
            <dd>{{ reservation.id }}</dd>
          </div>
          <div class="a-dl-row py-3 text-base">
            <dt class="text-grey-700">{{ t('reservations.row.item') }}</dt>
            <dd v-if="itemInfos.length" class="flex flex-col gap-3">
              <AItemCard v-for="item in itemInfos" :key="item.id" :item="item" compact />
            </dd>
            <dd v-else class="whitespace-pre-line">
              {{ reservation.summary.map(trSummary).join('\n') }}
            </dd>
          </div>
          <div
            v-if="
              reservation.pickupDeadline &&
              ['booked', 'submitted', 'confirmed'].includes(effectiveStatus(reservation))
            "
            class="a-dl-row py-3 text-base"
          >
            <dt class="text-grey-700">{{ t('reservations.row.pickup') }}</dt>
            <dd>
              {{ t('reservations.pickupBy', { date: deadlineText(reservation) })
              }}<span v-if="reservation.pickupDates?.length" class="block text-sm text-grey-700">
                {{ t('reservations.visitOn', { dates: pickupDatesText(reservation) }) }}
              </span>
            </dd>
          </div>
          <div class="a-dl-row py-3 text-base">
            <dt class="text-grey-700">{{ t('reservations.row.contact') }}</dt>
            <dd>{{ reservation.contactName }} {{ reservation.mobile }}</dd>
          </div>
        </dl>
      </ASection>
      <ASection v-if="center" :title="t('reservations.center')">
        <CenterCard :center="center" />
        <!-- 導航只在還要去中心取貨時有用；取消、逾期或評估維修（中心來電）只留撥打電話 -->
        <div class="mt-3 grid gap-2" :class="needsVisit ? 'grid-cols-2' : 'grid-cols-1'">
          <BaseButton outline @click="native.callPhone(center.phone)">
            {{ t('common.call') }}
          </BaseButton>
          <BaseButton v-if="needsVisit" outline @click="native.openMap(mapUrl(center))">
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

    <ADialog
      v-model="cancelledDialog"
      is-check
      :title="t('reservations.cancelledDialog.title')"
      :content="t('reservations.cancelledDialog.content', { id: reservation?.id ?? '' })"
    />
    <ADialog
      v-model="confirming"
      :title="t('reservations.cancelDialog.title')"
      :content="
        reservation?.service === 'borrow'
          ? t('reservations.cancelDialog.contentBorrow')
          : t('reservations.cancelDialog.contentAssess')
      "
      :negative-text="t('reservations.cancelDialog.keep')"
      :positive-text="t('reservations.cancelDialog.confirm')"
      @on-positive-click="doCancel"
    />
  </AStepPage>
</template>
