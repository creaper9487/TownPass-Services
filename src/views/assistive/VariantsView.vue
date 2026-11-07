<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AImage from '@/components/assistive/AImage.vue';
import StockError from '@/components/assistive/StockError.vue';
import AInput from '@/components/assistive/AInput.vue';
import AIcon from '@/components/assistive/AIcon.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import ACartBar from '@/components/assistive/ACartBar.vue';
import ADialog from '@/components/assistive/ADialog.vue';
import AItemCard from '@/components/assistive/AItemCard.vue';
import AErrorText from '@/components/assistive/AErrorText.vue';
import { ensurePush } from '@/utils/assistive/push';
import { t, tx, zhAttr } from '@/i18n/assistive';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveStockPolling } from '@/composables/useAssistiveStockPolling';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import {
  ArrivalError,
  fetchStock,
  fetchVariantFits,
  listArrivals,
  subscribeArrival,
  unsubscribeArrival
} from '@/utils/assistive/api';
import { catalog, variantInfo } from '@/utils/assistive/catalog';
import {
  HEIGHT_RANGE,
  WEIGHT_RANGE,
  hasHeight,
  hasWeight,
  matchFit,
  mergeFit
} from '@/utils/assistive/fit';
import type { Stock, Variant, VariantFit } from '@/utils/assistive/types';

const route = useRoute();
const router = useRouter();
const store = useAssistiveStore();
const flow = useAssistiveFlow();

const category = computed(() => catalog.value.find((c) => c.id === route.params.categoryId));
const stock = ref<Record<string, Stock>>({});
const loaded = ref(false);
const subscribed = ref(listArrivals().map((a) => a.variantId));

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
useAssistiveStockPolling((latest) => {
  if (loaded.value) stock.value = latest;
});

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
    error: valid ? '' : t('borrow.variants.fitRange', { min: range.min, max: range.max })
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
  if (!shown.value.length) return t('borrow.variants.fitNone');
  return unknown
    ? t('borrow.variants.fitMatchUnknown', { yes, unknown })
    : t('borrow.variants.fitMatch', { yes });
});
const clearFit = () => {
  store.fit = { height: '', weight: '' };
};

const inCart = (v: Variant) => store.variants.some((x) => x.id === v.id);

// 「預約」加入本次預約項目後留在這頁（底部顯示件數與「下一步」）；再按一次是取消加入。
const choose = (v: Variant) => {
  if (inCart(v)) {
    store.removeVariant(v.id);
    return;
  }
  store.addVariant({
    id: v.id,
    categoryName: category.value!.name,
    name: v.name,
    spec: specOf(v).join('、'),
    image: v.image ?? undefined
  });
};

// 到貨通知：在這裡按一下就登記，結果用彈窗告知（可以立刻取消登記），不另外開一頁確認。
const registering = ref<string | null>(null);
const arrivalError = ref<{ id: string; key: string } | null>(null);
const registered = ref<Variant | null>(null);
const registeredDialog = ref(false);
const registerArrival = async (v: Variant) => {
  if (subscribed.value.includes(v.id)) {
    router.push({ name: 'assistive-reservations' });
    return;
  }
  if (registering.value) return;
  registering.value = v.id;
  arrivalError.value = null;
  try {
    // 到貨是後端在補貨當下推播：先登記這支手機，到貨通知才收得到。
    await ensurePush();
    await subscribeArrival(v.id, v.name);
    subscribed.value = [...subscribed.value, v.id];
    registered.value = v;
    registeredDialog.value = true;
  } catch (e) {
    const code = e instanceof ArrivalError ? e.code : '';
    arrivalError.value = {
      id: v.id,
      key:
        code === 'DUPLICATE_WAITLIST'
          ? 'arrival.duplicate'
          : code === 'INVALID_FIELD'
            ? 'arrival.unavailable'
            : 'arrival.failed'
    };
  } finally {
    registering.value = null;
  }
};
const undoArrival = async () => {
  const v = registered.value;
  if (!v) return;
  try {
    await unsubscribeArrival(v.id);
    subscribed.value = subscribed.value.filter((id) => id !== v.id);
  } catch {
    arrivalError.value = { id: v.id, key: 'reservations.cancelFailed' };
  }
};
</script>

<template>
  <AStepPage
    v-if="category"
    :title="tx(category.name)"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <ASection>
      <details class="text-sm text-grey-700">
        <summary class="a11y-focus cursor-pointer font-semibold text-primary-700">
          {{ t('borrow.variants.noticeSummary') }}
        </summary>
        <p :lang="zhAttr" class="mt-2 leading-relaxed">
          圖片僅供參考，請以現場提供之輔具為主。若您所預約的輔具尺寸不合用，因輔具數量有限，若現場已無其他合適尺寸輔具則須另行預約借用。
        </p>
      </details>
    </ASection>
    <ASection v-if="noStockAtAll">
      <div class="rounded-lg border border-secondary-200 bg-secondary-50 p-4">
        <h2 class="tp-h3-semibold">
          {{ t('borrow.variants.noStock', { name: tx(category.name) }) }}
        </h2>
        <ul class="mt-3 flex flex-col gap-2 text-sm">
          <li>
            <RouterLink
              :to="{ name: 'assistive-need', params: { service: 'assess' } }"
              class="a11y-focus block min-h-12 rounded-lg bg-white p-3 font-semibold text-primary-700 underline"
              @click="store.begin('assess')"
            >
              {{ t('borrow.variants.assessLink') }}
            </RouterLink>
          </li>
        </ul>
      </div>
    </ASection>

    <ASection v-if="anyFitData && !failed" :title="t('borrow.variants.fitTitle')">
      <div class="a-grid-fit">
        <div class="grid grid-cols-2 gap-3">
          <AInput
            v-model="store.fit.height"
            :label="t('borrow.variants.height')"
            no-optional-mark
            inputmode="numeric"
            :maxlength="3"
            field-id="fit-height"
            :error="height.error"
          />
          <AInput
            v-model="store.fit.weight"
            :label="t('borrow.variants.weight')"
            no-optional-mark
            inputmode="numeric"
            :maxlength="3"
            field-id="fit-weight"
            :error="weight.error"
          />
        </div>
      </div>
      <p v-if="fitSummary" role="status" class="mt-3 text-sm text-grey-700">{{ fitSummary }}</p>
      <button
        v-if="store.fit.height || store.fit.weight"
        type="button"
        class="a11y-focus mt-2 min-h-11 text-base font-semibold text-primary-700 underline"
        @click="clearFit"
      >
        {{ t('borrow.variants.clearFit') }}
      </button>
    </ASection>
    <ASection v-if="failed">
      <StockError @retry="load" />
    </ASection>
    <ASection v-else grey>
      <ul class="flex flex-col gap-4">
        <li
          v-for="({ v, match }, i) in shown"
          :key="v.id"
          class="a-rise tp-card overflow-hidden"
          :style="{ '--i': Math.min(i, 6) }"
        >
          <AImage :src="v.image" hide-on-error class="h-44 p-3" />
          <div class="p-4" :class="{ 'border-t border-grey-100': true }">
            <h2 :lang="zhAttr" class="tp-h3-semibold">{{ v.name }}</h2>
            <ul v-if="specOf(v).length" class="mt-2 flex flex-wrap gap-1.5">
              <li v-for="s in specOf(v)" :key="s" :lang="zhAttr" class="tp-tag">
                {{ s }}
              </li>
            </ul>
            <p
              v-if="filterActive && match === 'unknown'"
              class="tp-tag mt-2 !border-grey-300 !text-grey-700"
            >
              {{ t('borrow.variants.fitUnknown') }}
            </p>
            <p v-if="v.description" :lang="zhAttr" class="mt-3 text-sm text-grey-700">
              {{ v.description }}
            </p>
            <p
              class="mt-3 flex items-center gap-1.5 text-base font-semibold"
              :class="loaded && !left(v) ? 'text-grey-700' : ''"
            >
              <template v-if="!loaded">&nbsp;</template>
              <template v-else>
                <AIcon
                  :name="left(v) ? 'check' : 'hourglass'"
                  class="h-[20px] w-[20px] shrink-0"
                  :class="left(v) ? 'text-primary-700' : ''"
                />
                {{ t('borrow.stockLeft', { n: left(v) }) }}
              </template>
            </p>
            <p
              v-if="loaded && !left(v) && waiting(v)"
              class="mt-0.5 flex items-center gap-1.5 text-base"
            >
              <AIcon name="people" class="h-[20px] w-[20px] shrink-0 text-grey-700" />
              {{ t('borrow.waiting', { n: waiting(v) }) }}
            </p>
            <BaseButton
              v-if="loaded && left(v) > 0"
              class="mt-3 w-full"
              :outline="inCart(v)"
              :aria-pressed="inCart(v)"
              @click="choose(v)"
            >
              <span class="inline-flex items-center gap-1.5">
                <AIcon v-if="inCart(v)" name="check" class="h-[20px] w-[20px] shrink-0" />
                {{ inCart(v) ? t('borrow.variants.added') : t('borrow.reserve') }}
              </span>
              <span class="sr-only">
                {{ t('borrow.srVariant', { category: tx(category.name), name: v.name }) }}
              </span>
            </BaseButton>
            <BaseButton
              v-else-if="loaded"
              outline
              class="mt-3 w-full"
              :aria-busy="registering === v.id"
              @click="registerArrival(v)"
            >
              {{
                subscribed.includes(v.id)
                  ? t('borrow.arrivalRegistered')
                  : t('borrow.arrivalNotice')
              }}<span class="sr-only">
                {{ t('borrow.srVariant', { category: tx(category.name), name: v.name }) }}
              </span>
            </BaseButton>
            <AErrorText v-if="arrivalError?.id === v.id">{{ t(arrivalError.key) }}</AErrorText>
          </div>
        </li>
      </ul>
    </ASection>
    <template v-if="store.variants.length" #footer>
      <ACartBar />
    </template>

    <ADialog
      v-model="registeredDialog"
      is-check
      :title="t('borrow.arrivalRegistered')"
      :negative-text="t('arrival.undo')"
      @on-negative-click="undoArrival"
    >
      <template #content>
        <AItemCard
          v-if="registered && variantInfo(registered.id)"
          :item="variantInfo(registered.id)!"
        />
        <p class="mt-3 text-base">{{ t('arrival.explain') }}</p>
      </template>
    </ADialog>
  </AStepPage>
</template>
