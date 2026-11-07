<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AChoice from '@/components/assistive/AChoice.vue';
import ClosureNotice from '@/components/assistive/ClosureNotice.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useTaipeiNow } from '@/utils/assistive/time';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import { fetchCenterStock } from '@/utils/assistive/api';
import type { CenterStockMap } from '@/utils/assistive/types';
import { useAssistiveLocate } from '@/composables/useAssistiveLocate';
import {
  centers,
  distanceKm,
  formatDate,
  hoursText,
  openDaysText
} from '@/utils/assistive/centers';

const store = useAssistiveStore();
const flow = useAssistiveFlow();
const { locate, locating, message } = useAssistiveLocate();
const error = ref('');

const now = useTaipeiNow();

// 逐日行事曆（國定假日、臨時休館）與這款在各中心的庫存；取不到就維持只看星期的做法，不拿分類總庫存代替。
const centerStock = ref<CenterStockMap | null>(null);
onMounted(async () => {
  store.loadCalendars();
  if (store.variant) centerStock.value = await fetchCenterStock(store.variant.id);
});
const rows = computed(() => {
  const loc = store.location;
  const rec = store.recommendedCenter;
  const sorted = [...centers].sort((a, b) =>
    loc
      ? distanceKm(a, loc.lat, loc.lng) - distanceKm(b, loc.lat, loc.lng)
      : a.id === rec?.id
        ? -1
        : b.id === rec?.id
          ? 1
          : 0
  );
  return sorted.map((c) => {
    const win = store.windowFor(c, now.value);
    const stockEntry = centerStock.value?.[c.id];
    const tag =
      c.id === rec?.id ? (store.recommendedBy === 'location' ? '離你最近' : `符合你的地址`) : '';
    const reach = loc ? `距離約 ${distanceKm(c, loc.lat, loc.lng).toFixed(1)} 公里` : '';
    // 休館時取貨期限會不會順延尚未確認，所以只標示「期限內沒有開館日」，不寫會順延。
    const closureText = win.closures
      .map((x) => `${formatDate(x.date)}休館${x.reason ? `：${x.reason}` : ''}`)
      .join('；');
    const pickup = win.openDates.length
      ? `取貨期限 ${formatDate(win.deadline)}，可前往：${win.openDates.map(formatDate).join('、')}`
      : `取貨期限 ${formatDate(win.deadline)} 前沒有開館，這家無法在期限內取貨`;
    const stockText = stockEntry
      ? stockEntry.stock > 0
        ? `● 這款剩 ${stockEntry.stock} 件`
        : '○ 這家目前沒有這款'
      : '';
    return {
      win,
      stock: stockEntry?.stock,
      option: {
        value: c.id,
        label: tag ? `${c.name}（${tag}）` : c.name,
        description: [
          c.address,
          `${openDaysText(c)} ${hoursText(c)}`,
          reach,
          pickup,
          closureText,
          stockText
        ]
          .filter(Boolean)
          .join('\n'),
        disabled: win.openDates.length === 0
      }
    };
  });
});
// 期限內可去的排前面，去不了的放最後
// 排序：期限內可去且有這款的 → 期限內可去（庫存未知）→ 可去但這家沒有這款 → 期限內去不了
const rank = (r: { option: { disabled: boolean }; stock?: number }) =>
  r.option.disabled ? 3 : r.stock === undefined ? 1 : r.stock > 0 ? 0 : 2;
const ordered = computed(() => [...rows.value].sort((a, b) => rank(a) - rank(b)));
const allClosed = computed(() => rows.value.every((r) => r.option.disabled));

const selected = computed<string>({
  get: () => store.centerId,
  set: (v) => {
    store.centerId = v;
    error.value = '';
  }
});

const next = () => {
  if (!store.centerId) {
    error.value = allClosed.value
      ? '這幾天三家中心都休館，請改天再預約。'
      : '請選擇一家取貨的輔具中心';
    return;
  }
  flow.goNext();
};
</script>

<template>
  <AStepPage
    title="選擇中心"
    lead="請選擇借用輔具中心"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <ASection v-if="store.closureNotices.length">
      <ClosureNotice :items="store.closureNotices" />
    </ASection>
    <ASection>
      <div v-if="!store.location" class="mb-4">
        <BaseButton outline class="w-full" :aria-busy="locating" @click="locate">
          依目前位置排序
        </BaseButton>
      </div>
      <p v-if="message" role="status" class="mb-3 text-sm text-grey-700">{{ message }}</p>
      <AChoice
        v-model="selected"
        legend="取貨中心"
        hide-legend
        required
        :error="error"
        :options="ordered.map((r) => r.option)"
      />
    </ASection>
    <template #footer>
      <BaseButton class="w-full !py-4" @click="next">下一步</BaseButton>
    </template>
  </AStepPage>
</template>
