<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AErrorText from '@/components/assistive/AErrorText.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import catalogJson from '@/data/assistive-catalog.json';
import { subscribeArrival, type ArrivalNotice } from '@/utils/assistive/api';
import type { Category } from '@/utils/assistive/types';

// 到貨通知：確認 → 送出 → 完成，和預約同樣有最後一次確認與明確的結果。
const route = useRoute();
const router = useRouter();

const found = computed(() => {
  for (const c of catalogJson as unknown as Category[]) {
    const v = c.variants.find((x) => x.id === route.params.variantId);
    if (v) {
      const specs = v.specs.filter((s) => s && s !== '---' && s !== '--' && s !== v.name);
      return { category: c, variant: v, label: [c.name, v.name, ...specs].join('・') };
    }
  }
  return null;
});

const sending = ref(false);
const failed = ref(false);
const done = ref<ArrivalNotice | null>(null);

const submit = async () => {
  if (!found.value || sending.value) return;
  sending.value = true;
  failed.value = false;
  try {
    done.value = await subscribeArrival(found.value.variant.id, found.value.label);
  } catch {
    failed.value = true;
  } finally {
    sending.value = false;
  }
};
</script>

<template>
  <AStepPage :title="done ? '已登記到貨通知' : '到貨通知'">
    <ASection v-if="!found">
      <p class="tp-h3-semibold">找不到這個輔具</p>
      <BaseButton class="mt-4 w-full" link :route-info="{ name: 'assistive-home' }">
        回輔具預約
      </BaseButton>
    </ASection>

    <template v-else-if="!done">
      <ASection>
        <div class="flex items-center justify-between">
          <h2 class="tp-h3-semibold text-primary-700">登記項目</h2>
        </div>
        <dl class="mt-2 divide-y divide-grey-100">
          <div class="grid grid-cols-[5rem_1fr] gap-3 py-3 text-base first:pt-1">
            <dt class="text-grey-700">輔具</dt>
            <dd class="break-words">{{ found.label }}</dd>
          </div>
        </dl>
        <AErrorText v-if="failed" class="mt-3">送出失敗，請檢查網路後再試一次。</AErrorText>
      </ASection>
    </template>

    <template v-else>
      <ASection>
        <div role="status" class="flex items-center gap-3 rounded-lg bg-primary-50 p-4">
          <img src="@/assets/images/check-icon-outline.svg" alt="" class="h-10 w-10 shrink-0" />
          <div>
            <p class="text-sm text-grey-700">登記編號</p>
            <p class="tp-h2 break-all">{{ done.id }}</p>
          </div>
        </div>
        <dl class="mt-3 divide-y divide-grey-100">
          <div class="grid grid-cols-[5rem_1fr] gap-3 py-3 text-base">
            <dt class="text-grey-700">輔具</dt>
            <dd class="break-words">{{ done.label }}</dd>
          </div>
        </dl>
      </ASection>
    </template>

    <template v-if="found" #footer>
      <div v-if="!done" class="grid grid-cols-2 gap-2">
        <BaseButton outline @click="router.back()">上一步</BaseButton>
        <BaseButton :aria-busy="sending" @click="submit">
          {{ sending ? '送出中…' : '確認送出' }}
        </BaseButton>
      </div>
      <div v-else class="grid grid-cols-2 gap-2">
        <BaseButton outline link :route-info="{ name: 'assistive-reservations' }">
          服務預約查詢與取消
        </BaseButton>
        <BaseButton link :route-info="{ name: 'assistive-home' }">回輔具預約</BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
