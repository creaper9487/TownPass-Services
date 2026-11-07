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
</script>

<template>
  <AStepPage
    title="選擇輔具"
    lead="請選擇你要的輔具，並於一小時內完成借用程序"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <ASection v-if="failed">
      <StockError @retry="load" />
    </ASection>
    <ASection v-else grey>
      <ul class="grid grid-cols-2 gap-3">
        <li v-for="c in catalog" :key="c.id" class="tp-card flex flex-col overflow-hidden">
          <AImage :src="c.image" hide-on-error class="h-32 p-2" />
          <div class="flex flex-1 flex-col p-3">
            <h2 class="text-base font-semibold">{{ c.name }}</h2>
            <p class="mt-1 text-base" :class="loaded && totals[c.id] === 0 ? 'text-grey-700' : ''">
              <template v-if="!loaded">&nbsp;</template>
              <template v-else>剩餘: {{ totals[c.id] }}</template>
            </p>
            <RouterLink
              v-if="loaded"
              :to="{ name: 'assistive-variants', params: { service: 'borrow', categoryId: c.id } }"
              class="a11y-focus mt-3 flex min-h-12 items-center justify-center rounded-lg px-3 text-base font-semibold"
              :class="
                totals[c.id] > 0
                  ? 'bg-primary-700 text-white'
                  : 'border border-primary-700 text-primary-700'
              "
            >
              {{ totals[c.id] > 0 ? '預約' : '到貨通知'
              }}<span class="sr-only">：{{ c.name }}</span>
            </RouterLink>
          </div>
        </li>
      </ul>
    </ASection>
  </AStepPage>
</template>
