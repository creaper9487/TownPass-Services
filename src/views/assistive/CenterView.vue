<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AChoice from '@/components/assistive/AChoice.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { t, tx } from '@/i18n/assistive';
import { useTaipeiNow } from '@/utils/assistive/time';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import { useAssistiveLocate } from '@/composables/useAssistiveLocate';
import {
  centerName,
  centers,
  distanceKm,
  formatDate,
  hoursText,
  openDaysText
} from '@/utils/assistive/centers';

const store = useAssistiveStore();
const flow = useAssistiveFlow();
const { locate, locating, message } = useAssistiveLocate();
const errorKey = ref('');
const error = computed(() => (errorKey.value ? t(errorKey.value) : ''));

const now = useTaipeiNow();

// 逐日行事曆（國定假日、臨時休館）；後端沒有分中心的庫存，所以中心卡片不寫庫存。
onMounted(() => store.loadCalendars());

// 取貨期限內中心沒開館時要不要擋下：後端目前關閉開館檢查（會收下這種預約），網頁預設跟著放行，只顯示提醒；
// 要恢復擋下，在 .env 設 VITE_ASSISTIVE_ENFORCE_OPENING=1。
const enforceOpening = import.meta.env.VITE_ASSISTIVE_ENFORCE_OPENING === '1';
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
    const tag =
      c.id === rec?.id
        ? store.recommendedBy === 'location'
          ? t('center.nearest')
          : t('center.matchAddress')
        : '';
    const reach = loc
      ? t('center.distance', { km: distanceKm(c, loc.lat, loc.lng).toFixed(1) })
      : '';
    // 休館時取貨期限會不會順延尚未確認，所以只標示「期限內沒有開館日」，不寫會順延。
    const closureText = win.closures
      .map((x) =>
        x.reason
          ? t('center.closedReason', { date: formatDate(x.date), reason: tx(x.reason) })
          : t('center.closed', { date: formatDate(x.date) })
      )
      .join(t('center.sepSemi'));
    const pickup = win.openDates.length
      ? t('center.pickup', {
          deadline: formatDate(win.deadline),
          dates: win.openDates.map(formatDate).join(t('center.sepList'))
        })
      : t('center.pickupNone', { deadline: formatDate(win.deadline) });
    return {
      win,
      option: {
        value: c.id,
        label: tag ? t('center.nameTag', { name: centerName(c), tag }) : centerName(c),
        description: [c.address, `${openDaysText(c)} ${hoursText(c)}`, reach, pickup, closureText]
          .filter(Boolean)
          .join('\n'),
        disabled: enforceOpening && win.openDates.length === 0
      }
    };
  });
});
// 期限內可去的排前面，去不了的放最後
const rank = (r: { win: { openDates: Date[] } }) => (r.win.openDates.length ? 0 : 1);
const ordered = computed(() => [...rows.value].sort((a, b) => rank(a) - rank(b)));
const allClosed = computed(() => rows.value.every((r) => r.win.openDates.length === 0));

// 三家中心在取貨期限內都沒有開館（例如週六晚上、隔天週日休館）：直接告訴使用者哪天可以再來，
// 而不是只留下三張灰掉的卡片。從明天起逐日找，第一個有中心開館的日子就是答案。
const nextOpenDate = computed(() => {
  if (!allClosed.value) return null;
  const today = now.value;
  for (let i = 1; i <= 14; i++) {
    const morning = new Date(today.getFullYear(), today.getMonth(), today.getDate() + i, 8, 0);
    const firsts = centers
      .map((c) => store.windowFor(c, morning).openDates[0])
      .filter((d): d is Date => !!d);
    if (firsts.length) return firsts.reduce((a, b) => (a.getTime() <= b.getTime() ? a : b));
  }
  return null;
});

const selected = computed<string>({
  get: () => store.centerId,
  set: (v) => {
    store.centerId = v;
    errorKey.value = '';
  }
});

const next = () => {
  if (!store.centerId) {
    errorKey.value = enforceOpening && allClosed.value ? 'center.allClosed' : 'center.pickRequired';
    return;
  }
  flow.goNext();
};
</script>

<template>
  <AStepPage
    :title="t('center.title')"
    :lead="t('center.lead')"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <!-- 休館公告不在這裡重複：每家中心的卡片已列出取貨期限內的休館日 -->
    <ASection>
      <div v-if="!store.location" class="mb-4">
        <BaseButton outline class="w-full" :aria-busy="locating" @click="locate">
          {{ t('center.locate') }}
        </BaseButton>
      </div>
      <p
        v-if="allClosed"
        role="status"
        class="mb-4 rounded-lg border border-orange-700 bg-orange-50 p-3 text-base text-orange-800"
      >
        {{
          nextOpenDate
            ? t(enforceOpening ? 'center.allClosedNext' : 'center.allClosedWarn', {
                date: formatDate(nextOpenDate)
              })
            : t('center.allClosed')
        }}
      </p>
      <p v-if="message" role="status" class="mb-3 text-sm text-grey-700">{{ message }}</p>
      <AChoice
        v-model="selected"
        :legend="t('center.legend')"
        hide-legend
        required
        :error="error"
        :options="ordered.map((r) => r.option)"
      />
    </ASection>
    <template #footer>
      <BaseButton class="w-full !py-4" @click="next">{{ t('common.next') }}</BaseButton>
    </template>
  </AStepPage>
</template>
