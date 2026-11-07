<script setup lang="ts">
import { t, trSummary } from '@/i18n/assistive';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow, stepRoute } from '@/composables/useAssistiveFlow';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AItemCard from '@/components/assistive/AItemCard.vue';
import { selectedInfo } from '@/utils/assistive/catalog';
import BaseButton from '@/components/atoms/BaseButton.vue';

// 官方「本次預約項目」：可以一次借好幾件，再一起選中心。
const store = useAssistiveStore();
const flow = useAssistiveFlow();

// 儲存的品名一律是中文；顯示時類別才翻成當下語言
const label = (v: { categoryName: string; name: string; spec: string }) => trSummary(v.name);
</script>

<template>
  <AStepPage :title="t('borrow.cart.title')" :step="flow.current.value" :total="flow.total.value">
    <ASection grey>
      <p v-if="!store.variants.length" class="text-base">{{ t('borrow.cart.empty') }}</p>
      <ul v-else class="flex flex-col gap-3">
        <li
          v-for="v in store.variants"
          :key="v.id"
          class="a-rise tp-card flex flex-wrap items-center gap-3 p-3"
        >
          <!-- 文字放大後，刪除按鈕換到下一行，不跟品名搶寬度 -->
          <AItemCard :item="selectedInfo(v)" class="min-w-[12rem] flex-1" />
          <BaseButton outline class="ml-auto shrink-0" @click="store.removeVariant(v.id)">
            {{ t('borrow.cart.remove')
            }}<span class="sr-only">{{ t('borrow.srItem', { text: label(v) }) }}</span>
          </BaseButton>
        </li>
      </ul>
    </ASection>

    <template #footer>
      <div class="grid grid-cols-2 gap-2">
        <BaseButton outline link :route-info="stepRoute('borrow', 'items')">
          {{ t('borrow.cart.more') }}
        </BaseButton>
        <BaseButton :disabled="!store.variants.length" @click="flow.goNext()">
          {{ t('common.next') }}
        </BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
