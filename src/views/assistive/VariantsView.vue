<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AImage from '@/components/assistive/AImage.vue';
import StockError from '@/components/assistive/StockError.vue';
import AInput from '@/components/assistive/AInput.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow, stepRoute } from '@/composables/useAssistiveFlow';
import { fetchStock, fetchVariantFits, listArrivals } from '@/utils/assistive/api';
import catalogJson from '@/data/assistive-catalog.json';
import {
  HEIGHT_RANGE,
  WEIGHT_RANGE,
  hasHeight,
  hasWeight,
  matchFit,
  mergeFit
} from '@/utils/assistive/fit';
import type { Category, Stock, Variant, VariantFit } from '@/utils/assistive/types';

const route = useRoute();
const router = useRouter();
const store = useAssistiveStore();
const flow = useAssistiveFlow();

const category = computed(() =>
  (catalogJson as unknown as Category[]).find((c) => c.id === route.params.categoryId)
);
const stock = ref<Record<string, Stock>>({});
const loaded = ref(false);
const subscribed = listArrivals().map((a) => a.variantId);

const failed = ref(false);
const remoteFits = ref<Record<string, VariantFit> | null>(null);

const load = async () => {
  failed.value = false;
  try {
    stock.value = await fetchStock();
    remoteFits.value = await fetchVariantFits();
    loaded.value = true;
  } catch {
    failed.value = true;
  }
};
onMounted(load);

const specOf = (v: Variant) =>
  v.specs.filter((s) => s && s !== '---' && s !== '--' && s !== v.name);
const left = (v: Variant) => stock.value[v.id]?.stock ?? 0;
const waiting = (v: Variant) => stock.value[v.id]?.waiting ?? 0;

// 有庫存的排前面，沒庫存的依等待人數少到多
const variants = computed(() =>
  [...(category.value?.variants ?? [])].sort((a, b) => {
    const [sa, sb] = [left(a) > 0, left(b) > 0];
    return sa === sb ? (sa ? 0 : waiting(a) - waiting(b)) : sa ? -1 : 1;
  })
);
const noStockAtAll = computed(() => loaded.value && variants.value.every((v) => left(v) === 0));

// ---- 依身高與體重篩選款式 ----
const fitOf = (v: Variant) => mergeFit(v, remoteFits.value?.[v.id]);
const anyFitData = computed(() =>
  (category.value?.variants ?? []).some((v) => hasHeight(fitOf(v)) || hasWeight(fitOf(v)))
);
const parseField = (raw: string, range: { min: number; max: number }) => {
  const text = raw.trim();
  if (!text) return { value: undefined, error: '' };
  const n = Number(text);
  const valid = Number.isInteger(n) && n >= range.min && n <= range.max;
  return {
    value: valid ? n : undefined,
    error: valid ? '' : `請輸入 ${range.min}–${range.max} 之間的整數`
  };
};
const height = computed(() => parseField(store.fit.height, HEIGHT_RANGE));
const weight = computed(() => parseField(store.fit.weight, WEIGHT_RANGE));
const filterActive = computed(
  () => height.value.value !== undefined || weight.value.value !== undefined
);
const shown = computed(() =>
  variants.value
    .map((v) => ({ v, match: matchFit(fitOf(v), height.value.value, weight.value.value) }))
    .filter((x) => !filterActive.value || x.match !== 'no')
);
const fitSummary = computed(() => {
  if (!filterActive.value) return '';
  const yes = shown.value.filter((x) => x.match === 'yes').length;
  const unknown = shown.value.filter((x) => x.match === 'unknown').length;
  if (!shown.value.length) return '沒有符合的款式';
  return `符合 ${yes} 款${unknown ? `，${unknown} 款未標示` : ''}`;
});
const clearFit = () => {
  store.fit = { height: '', weight: '' };
};

const choose = (v: Variant) => {
  store.variant = {
    id: v.id,
    categoryName: category.value!.name,
    name: v.name,
    spec: specOf(v).join('、')
  };
  router.push(stepRoute('borrow', 'center'));
};
</script>

<template>
  <AStepPage
    v-if="category"
    title="選擇種類"
    lead="「圖片僅供參考，請以現場提供之輔具為主。若您所預約的輔具尺寸不合用，因輔具數量有限，若現場已無其他合適尺寸輔具則須另行預約借用。」"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <ASection v-if="noStockAtAll">
      <div class="rounded-lg border border-secondary-200 bg-secondary-50 p-4">
        <h2 class="tp-h3-semibold">目前二手{{ category.name }}都沒有庫存</h2>
        <ul class="mt-3 flex flex-col gap-2 text-sm">
          <li>
            <RouterLink
              :to="{ name: 'assistive-need', params: { service: 'assess' } }"
              class="a11y-focus block min-h-12 rounded-lg bg-white p-3 font-semibold text-primary-700 underline"
              @click="store.begin('assess')"
            >
              預約輔具評估，了解購買或租賃補助
            </RouterLink>
          </li>
        </ul>
      </div>
    </ASection>

    <ASection v-if="anyFitData && !failed">
      <div class="grid grid-cols-2 gap-3">
        <AInput
          v-model="store.fit.height"
          label="身高（公分）"
          inputmode="numeric"
          :maxlength="3"
          field-id="fit-height"
          :error="height.error"
        />
        <AInput
          v-model="store.fit.weight"
          label="體重（公斤）"
          inputmode="numeric"
          :maxlength="3"
          field-id="fit-weight"
          :error="weight.error"
        />
      </div>
      <p v-if="fitSummary" role="status" class="mt-3 text-sm text-grey-700">{{ fitSummary }}</p>
      <button
        v-if="store.fit.height || store.fit.weight"
        type="button"
        class="a11y-focus mt-2 min-h-11 text-base font-semibold text-primary-700 underline"
        @click="clearFit"
      >
        清除篩選
      </button>
    </ASection>
    <ASection v-if="failed">
      <StockError @retry="load" />
    </ASection>
    <ASection v-else grey>
      <ul class="flex flex-col gap-4">
        <li v-for="{ v, match } in shown" :key="v.id" class="tp-card overflow-hidden">
          <AImage :src="v.image" hide-on-error class="h-44 p-3" />
          <div class="p-4" :class="{ 'border-t border-grey-100': true }">
            <h2 class="tp-h3-semibold">{{ v.name }}</h2>
            <ul v-if="specOf(v).length" class="mt-2 flex flex-wrap gap-1.5">
              <li v-for="s in specOf(v)" :key="s" class="tp-tag">
                {{ s }}
              </li>
            </ul>
            <p
              v-if="filterActive && match === 'unknown'"
              class="tp-tag mt-2 !border-grey-300 !text-grey-700"
            >
              未標示適用身高體重
            </p>
            <p v-if="v.description" class="mt-3 text-sm text-grey-700">
              {{ v.description }}
            </p>
            <p
              class="mt-3 text-base font-semibold"
              :class="{ 'text-grey-700': loaded && !left(v) }"
            >
              <template v-if="!loaded">&nbsp;</template>
              <template v-else>剩餘: {{ left(v) }}</template>
            </p>
            <p v-if="loaded && !left(v) && waiting(v)" class="text-base">
              等待人數：{{ waiting(v) }}
            </p>
            <BaseButton v-if="loaded && left(v) > 0" class="mt-3 w-full" @click="choose(v)">
              預約<span class="sr-only">：{{ category.name }}，{{ v.name }}</span>
            </BaseButton>
            <BaseButton
              v-else-if="loaded"
              outline
              class="mt-3 w-full"
              @click="
                router.push(
                  subscribed.includes(v.id)
                    ? { name: 'assistive-reservations' }
                    : { name: 'assistive-arrival', params: { variantId: v.id } }
                )
              "
            >
              {{ subscribed.includes(v.id) ? '已登記到貨通知' : '到貨通知'
              }}<span class="sr-only">：{{ category.name }}，{{ v.name }}</span>
            </BaseButton>
          </div>
        </li>
      </ul>
    </ASection>
  </AStepPage>
</template>
