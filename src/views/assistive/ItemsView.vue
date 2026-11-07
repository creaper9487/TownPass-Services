<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AIcon from '@/components/assistive/AIcon.vue';
import AImage from '@/components/assistive/AImage.vue';
import StockError from '@/components/assistive/StockError.vue';
import { t, tx } from '@/i18n/assistive';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import ACartBar from '@/components/assistive/ACartBar.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveStockPolling } from '@/composables/useAssistiveStockPolling';
import { fetchStock } from '@/utils/assistive/api';
import { catalog } from '@/utils/assistive/catalog';
import type { Stock } from '@/utils/assistive/types';

const flow = useAssistiveFlow();
const store = useAssistiveStore();
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
useAssistiveStockPolling((latest) => {
  if (loaded.value) stock.value = latest;
});

const totals = computed(() =>
  Object.fromEntries(
    catalog.value.map((c) => [
      c.id,
      c.variants.reduce((sum, v) => sum + (stock.value[v.id]?.stock ?? 0), 0)
    ])
  )
);
</script>

<template>
  <AStepPage
    :title="t('borrow.items.title')"
    :lead="t('borrow.items.lead')"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <ASection v-if="failed">
      <StockError @retry="load" />
    </ASection>
    <ASection v-else grey>
      <!-- 文字放大後兩欄太窄，改成一欄（見 index.css 的 a-grid-fit） -->
      <div class="a-grid-fit">
        <ul class="grid grid-cols-2 gap-3">
          <li
            v-for="(c, i) in catalog"
            :key="c.id"
            class="a-rise tp-card flex flex-col overflow-hidden"
            :style="{ '--i': Math.min(i, 8) }"
          >
            <AImage :src="c.image" hide-on-error class="h-[128px] p-2" />
            <div class="flex flex-1 flex-col p-3">
              <h2 class="text-base font-semibold">{{ tx(c.name) }}</h2>
              <p
                class="mt-1 flex items-center gap-1.5 text-base"
                :class="loaded && totals[c.id] === 0 ? 'text-grey-700' : ''"
              >
                <template v-if="!loaded">&nbsp;</template>
                <template v-else>
                  <AIcon
                    :name="totals[c.id] ? 'check' : 'hourglass'"
                    class="h-[20px] w-[20px] shrink-0"
                    :class="totals[c.id] ? 'text-primary-700' : ''"
                  />
                  {{ t('borrow.stockLeft', { n: totals[c.id] }) }}
                </template>
              </p>
              <RouterLink
                v-if="loaded"
                :to="{
                  name: 'assistive-variants',
                  params: { service: 'borrow', categoryId: c.id }
                }"
                class="a11y-focus mt-3 flex min-h-12 items-center justify-center rounded-lg px-3 text-base font-semibold"
                :class="
                  totals[c.id] > 0
                    ? 'bg-primary-700 text-white'
                    : 'border border-primary-700 text-primary-700'
                "
              >
                {{ totals[c.id] > 0 ? t('borrow.reserve') : t('borrow.arrivalNotice')
                }}<span class="sr-only">{{ t('borrow.srItem', { text: tx(c.name) }) }}</span>
              </RouterLink>
            </div>
          </li>
        </ul>
      </div>
    </ASection>
    <template v-if="store.variants.length" #footer>
      <ACartBar />
    </template>
  </AStepPage>
</template>
