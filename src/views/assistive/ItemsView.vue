<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AImage from '@/components/assistive/AImage.vue';
import StockError from '@/components/assistive/StockError.vue';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import { fetchStock } from '@/utils/assistive/api';
import catalogJson from '@/data/assistive-catalog.json';
import stockMeta from '@/data/assistive-stock.json';
import type { Category, Stock } from '@/utils/assistive/types';

const flow = useAssistiveFlow();
const catalog = catalogJson as Category[];
const stock = ref<Record<string, Stock>>({});
const loaded = ref(false);
const failed = ref(false);

const load = async () => {
  failed.value = false;
  try {
    stock.value = await fetchStock();
    loaded.value = true;
  } catch {
    failed.value = true;
  }
};
onMounted(load);

const totals = computed(() =>
  Object.fromEntries(
    catalog.map((c) => [
      c.id,
      c.variants.reduce((sum, v) => sum + (stock.value[v.id]?.stock ?? 0), 0)
    ])
  )
);
const asOf = computed(() => stockMeta.asOf.slice(5).replace('-', '/'));
</script>

<template>
  <AStepPage
    title="你想借哪一類輔具？"
    lead="先選類別，下一頁再挑尺寸與款式。"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <ASection v-if="failed">
      <StockError @retry="load" />
    </ASection>
    <ASection v-else grey>
      <ul class="grid grid-cols-2 gap-3">
        <li v-for="c in catalog" :key="c.id">
          <RouterLink
            :to="{ name: 'assistive-variants', params: { service: 'borrow', categoryId: c.id } }"
            class="a11y-focus tp-card flex h-full flex-col overflow-hidden"
          >
            <AImage :src="c.image" class="h-32 p-2" />
            <span class="flex flex-1 flex-col border-t border-grey-100 p-3">
              <span class="text-base font-semibold">{{ c.name }}</span>
              <span
                class="mt-1 text-sm"
                :class="totals[c.id] > 0 ? 'text-primary-800' : 'text-grey-700'"
              >
                <template v-if="!loaded">&nbsp;</template>
                <template v-else-if="totals[c.id] > 0">● 剩餘 {{ totals[c.id] }} 件</template>
                <template v-else>○ 目前無庫存</template>
              </span>
              <span class="mt-0.5 text-sm text-grey-700">{{ c.variants.length }} 種款式</span>
            </span>
          </RouterLink>
        </li>
      </ul>
      <p class="mt-4 text-sm text-grey-700">庫存為 {{ asOf }} 的資料，實際以預約當下為準。</p>
    </ASection>
  </AStepPage>
</template>
