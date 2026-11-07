<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AImage from '@/components/assistive/AImage.vue';
import StockError from '@/components/assistive/StockError.vue';
import AInput from '@/components/assistive/AInput.vue';
import RentalStoreList from '@/components/assistive/RentalStoreList.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow, stepRoute } from '@/composables/useAssistiveFlow';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import {
  arrivalSubscriptions,
  fetchRentalStores,
  fetchStock,
  fetchVariantFits,
  subscribeArrival,
  unsubscribeArrival
} from '@/utils/assistive/api';
import catalogJson from '@/data/assistive-catalog.json';
import {
  HEIGHT_RANGE,
  WEIGHT_RANGE,
  hasHeight,
  hasWeight,
  matchFit,
  mergeFit
} from '@/utils/assistive/fit';
import type { Category, RentalStore, Stock, Variant, VariantFit } from '@/utils/assistive/types';

const route = useRoute();
const router = useRouter();
const store = useAssistiveStore();
const flow = useAssistiveFlow();
const native = useAssistiveNative();

const category = computed(() =>
  (catalogJson as unknown as Category[]).find((c) => c.id === route.params.categoryId)
);
const stock = ref<Record<string, Stock>>({});
const subscribed = ref<string[]>([]);
const loaded = ref(false);
const status = ref<Record<string, string>>({});

const failed = ref(false);
const remoteFits = ref<Record<string, VariantFit> | null>(null);
const rentalStores = ref<RentalStore[] | null>(null);
let rentalRequested = false;

const load = async () => {
  failed.value = false;
  try {
    stock.value = await fetchStock();
    subscribed.value = arrivalSubscriptions();
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

// 全部缺貨時，嘗試取得附近的民間租賃特約門市；沒資料就維持原本的「輔具哪裡找」連結。
watch(
  noStockAtAll,
  async (empty) => {
    if (!empty || rentalRequested || !category.value) return;
    rentalRequested = true;
    rentalStores.value = await fetchRentalStores(category.value.id);
  },
  { immediate: true }
);

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
  if (!shown.value.length) return '沒有符合的款式，可以調整身高或體重，或清除篩選。';
  return `符合 ${yes} 款${unknown ? `；另有 ${unknown} 款沒有標示適用身高體重，也一併列出` : ''}。`;
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

const arrivalName = (v: Variant) => [category.value!.name, v.name, ...specOf(v)].join('・');

const toggleArrival = async (v: Variant) => {
  const on = subscribed.value.includes(v.id);
  if (on) {
    await unsubscribeArrival(v.id);
    subscribed.value = subscribed.value.filter((id) => id !== v.id);
    native.notify('訂閱通知', `已取消訂閱${arrivalName(v)}到貨通知`);
    status.value = { ...status.value, [v.id]: '已取消到貨通知。' };
  } else {
    await subscribeArrival(v.id);
    subscribed.value = [...subscribed.value, v.id];
    native.notify('訂閱通知', `已訂閱${arrivalName(v)}到貨通知`);
    status.value = { ...status.value, [v.id]: '已登記，有庫存時會通知你。' };
  }
};

const FIND_URL = 'https://tpap.gov.taipei/app37/whereVehicleView/index';
</script>

<template>
  <AStepPage
    v-if="category"
    :title="`${category.name}要選哪一種？`"
    lead="看照片、尺寸與適用對象，挑最接近需求的款式。"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <ASection v-if="noStockAtAll">
      <div class="rounded-lg border border-secondary-200 bg-secondary-50 p-4">
        <h2 class="tp-h3-semibold">目前二手{{ category.name }}都沒有庫存</h2>
        <p class="mt-1 text-sm">如果需要得急，可以考慮：</p>
        <ul class="mt-2 flex flex-col gap-2 text-sm">
          <li class="rounded-lg bg-white p-3">先登記想要款式的到貨通知，有庫存會通知你。</li>
          <li>
            <RouterLink
              :to="{ name: 'assistive-qualify', params: { service: 'assess' } }"
              class="a11y-focus block min-h-12 rounded-lg bg-white p-3 font-semibold text-primary-700 underline"
              @click="store.begin('assess')"
            >
              預約輔具評估，了解購買或租賃補助
            </RouterLink>
          </li>
          <li v-if="rentalStores" class="rounded-lg bg-white p-3">
            向民間廠商租賃：下方是附近的特約門市。
          </li>
          <li v-else>
            <button
              type="button"
              class="a11y-focus block min-h-12 w-full rounded-lg bg-white p-3 text-left font-semibold text-primary-700 underline"
              @click="native.openLink(FIND_URL)"
            >
              向民間廠商租賃：到「輔具哪裡找」看廠商
            </button>
          </li>
        </ul>
        <RentalStoreList v-if="rentalStores" :stores="rentalStores" class="mt-4" />
      </div>
    </ASection>

    <ASection
      v-if="anyFitData && !failed"
      title="照身高體重找適用款"
      hint="輸入身高與體重，只顯示適用的款式；沒有標示的款式也會一併列出。"
    >
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
              :class="left(v) > 0 ? 'text-primary-800' : 'text-grey-700'"
            >
              <template v-if="!loaded">&nbsp;</template>
              <template v-else-if="left(v) > 0">● 剩餘 {{ left(v) }} 件</template>
              <template v-else>
                ○ 目前無庫存<span v-if="waiting(v)" class="font-normal">
                  ，{{ waiting(v) }} 人等待中
                </span>
              </template>
            </p>
            <BaseButton v-if="loaded && left(v) > 0" class="mt-3 w-full" @click="choose(v)">
              預約這個<span class="sr-only">：{{ category.name }}，{{ v.name }}</span>
            </BaseButton>
            <BaseButton v-else-if="loaded" outline class="mt-3 w-full" @click="toggleArrival(v)">
              {{ subscribed.includes(v.id) ? '✓ 已登記到貨通知（點一下取消）' : '到貨時通知我' }}
              <span class="sr-only">：{{ category.name }}，{{ v.name }}</span>
            </BaseButton>
            <p
              v-if="status[v.id]"
              role="status"
              class="mt-2 text-sm font-semibold text-primary-800"
            >
              {{ status[v.id] }}
            </p>
          </div>
        </li>
      </ul>
    </ASection>
  </AStepPage>
</template>
