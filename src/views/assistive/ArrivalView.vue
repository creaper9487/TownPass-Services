<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AErrorText from '@/components/assistive/AErrorText.vue';
import AItemCard from '@/components/assistive/AItemCard.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { catalog, variantInfo } from '@/utils/assistive/catalog';
import { t, trSummary } from '@/i18n/assistive';
import { ArrivalError, subscribeArrival, type ArrivalNotice } from '@/utils/assistive/api';
import { ensurePush } from '@/utils/assistive/push';

// 到貨通知：確認 → 送出 → 完成，和預約同樣有最後一次確認與明確的結果。
const route = useRoute();
const router = useRouter();

const found = computed(() => {
  for (const c of catalog.value) {
    const v = c.variants.find((x) => x.id === route.params.variantId);
    if (v) {
      return { category: c, variant: v, label: v.name };
    }
  }
  return null;
});

const sending = ref(false);
const failed = ref(false);
// 同一類已經有登記、品項不開放，和連不上要分開說明
const failureKey = ref('arrival.failed');
const done = ref<ArrivalNotice | null>(null);
const info = computed(() => (found.value ? variantInfo(found.value.variant.id) : undefined));

const submit = async () => {
  if (!found.value || sending.value) return;
  sending.value = true;
  failed.value = false;
  try {
    // 到貨是後端在庫存補貨的當下推播：先登記這支手機，到貨通知才收得到。
    await ensurePush();
    done.value = await subscribeArrival(found.value.variant.id, found.value.label);
  } catch (e) {
    const code = e instanceof ArrivalError ? e.code : '';
    failureKey.value =
      code === 'DUPLICATE_WAITLIST'
        ? 'arrival.duplicate'
        : code === 'INVALID_FIELD'
          ? 'arrival.unavailable'
          : 'arrival.failed';
    failed.value = true;
  } finally {
    sending.value = false;
  }
};
</script>

<template>
  <AStepPage :title="done ? t('borrow.arrivalRegistered') : t('borrow.arrivalNotice')">
    <ASection v-if="!found">
      <p class="tp-h3-semibold">{{ t('arrival.notFound') }}</p>
      <BaseButton class="mt-4 w-full" link :route-info="{ name: 'assistive-home' }">
        {{ t('arrival.home') }}
      </BaseButton>
    </ASection>

    <template v-else-if="!done">
      <ASection>
        <div class="flex items-center justify-between">
          <h2 class="tp-h3-semibold text-primary-700">{{ t('arrival.registerHeading') }}</h2>
        </div>
        <p class="mt-3 text-base text-grey-700">{{ t('arrival.device') }}</p>
        <AItemCard v-if="info" :item="info" class="mt-2" />
        <p v-else class="mt-2 break-words text-base font-semibold">{{ trSummary(found.label) }}</p>
        <p class="mt-4 text-base">{{ t('arrival.explain') }}</p>
        <AErrorText v-if="failed" class="mt-3">{{ t(failureKey) }}</AErrorText>
      </ASection>
    </template>

    <template v-else>
      <ASection>
        <div role="status" class="flex items-center gap-3 rounded-lg bg-primary-50 p-4">
          <img
            src="@/assets/images/check-icon-outline.svg"
            alt=""
            class="a-pop h-10 w-10 shrink-0"
          />
          <div>
            <p class="text-sm text-grey-700">{{ t('arrival.number') }}</p>
            <p class="tp-h2 break-all">{{ done.id }}</p>
          </div>
        </div>
        <p class="mt-4 text-base text-grey-700">{{ t('arrival.device') }}</p>
        <AItemCard v-if="info" :item="info" class="mt-2" />
        <p v-else class="mt-2 break-words text-base font-semibold">{{ trSummary(done.label) }}</p>
      </ASection>
    </template>

    <template v-if="found" #footer>
      <div v-if="!done" class="grid grid-cols-2 gap-2">
        <BaseButton outline @click="router.back()">{{ t('common.prev') }}</BaseButton>
        <BaseButton :aria-busy="sending" @click="submit">
          {{ sending ? t('arrival.sending') : t('arrival.submit') }}
        </BaseButton>
      </div>
      <div v-else class="grid grid-cols-2 gap-2">
        <BaseButton outline link :route-info="{ name: 'assistive-reservations' }">
          {{ t('arrival.reservations') }}
        </BaseButton>
        <BaseButton link :route-info="{ name: 'assistive-home' }">
          {{ t('arrival.home') }}
        </BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
