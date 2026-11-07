<script setup lang="ts">
import { computed, ref } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AChoice from '@/components/assistive/AChoice.vue';
import AIcon, { type IconName } from '@/components/assistive/AIcon.vue';
import AInput from '@/components/assistive/AInput.vue';
import ErrorSummary from '@/components/assistive/ErrorSummary.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import ServiceTabs from '@/components/molecules/ServiceTabs.vue';
import { catalog } from '@/utils/assistive/catalog';
import type { SummaryItem } from '@/utils/assistive/validators';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { services, serviceShortTitle, type NeedGroup } from '@/utils/assistive/services';
import { t, tx, zhAttr } from '@/i18n/assistive';

// 官方表單：申請評估、申請維修（同一張表）／申請回收。說明與勾選項名稱照官方原文。
const store = useAssistiveStore();
const flow = useAssistiveFlow();
const native = useAssistiveNative();
// 把公告切成「文字、電話、文字、電話…」：奇數位置是電話號碼
const phoneParts = (text: string) => text.split(/(\d{2}-\d{4}-\d{4})/);
const groups = computed(() => services[flow.service.value].groups ?? []);
// 區塊標題（申請評估、申請維修）是介面文字，跟著語言；g.title 是官方中文原名
const groupTitle = (g: NeedGroup) => t(`need.group.${g.id}`);

const listOf = (g: NeedGroup) => (g.id === 'repair' ? store.repairNeeds : store.needs);
const setList = (g: NeedGroup, v: string[]) => {
  if (g.id === 'repair') store.repairNeeds = v;
  else store.needs = v;
};
const otherOf = (g: NeedGroup) => (g.id === 'repair' ? store.repairOther : store.needOther);
const setOther = (g: NeedGroup, v: string) => {
  if (g.id === 'repair') store.repairOther = v;
  else store.needOther = v;
};
// 官方借用頁已有照片的品項，勾選項目直接帶同一張照片；沒有官方照片的品項（例如電動輪椅）不放，免得配錯圖。
const photoCategory: Record<string, string> = {
  '居家用照顧床(病床)': '居家用照顧床',
  氣墊床: '氣墊床',
  輪椅座墊: '輪椅座墊',
  手動輪椅: '輪椅',
  '拐杖/助行器': '助行器',
  便盆椅: '便盆椅'
};
const photoOf = (option: string) =>
  catalog.value.find((c) => c.name === photoCategory[option])?.image ?? undefined;

// 沒有官方照片的品項改放線條圖示：每一列右側都有一塊縮圖，版面整齊；圖示只裝飾，名稱仍是文字。
const iconOf: Record<string, IconName> = {
  電動輪椅: 'wheelchair',
  居家無障礙: 'home',
  '矯具/義具': 'brace',
  視障輔具: 'eye',
  溝通輔具: 'chat',
  電腦輔具: 'monitor',
  爬梯機借用: 'stairs'
};

const optionsOf = (g: NeedGroup) => [
  ...g.options.map((o) => ({ value: o, label: tx(o), image: photoOf(o), icon: iconOf[o] })),
  ...(g.other ? [{ value: '其他', label: tx('其他'), icon: 'more' as IconName }] : [])
];

// 申請評估、申請維修分頁；別頁已勾選的數量顯示在分頁標籤上，不會看不到。
const tabs = computed(() =>
  groups.value.map((g) => {
    const n = listOf(g).length;
    return {
      id: g.id,
      title: n ? t('need.tabCount', { title: groupTitle(g), n }) : groupTitle(g),
      label: n ? t('need.tabCountLabel', { title: groupTitle(g), n }) : undefined
    };
  })
);
const activeTab = ref(
  Math.max(
    0,
    groups.value.findIndex((g) => listOf(g).length)
  )
);
const activeGroup = computed(() => groups.value[activeTab.value]);

// 錯誤摘要跟其他頁一樣：role=alert、移焦點、每一項連到欄位（不放在清單底下，免得按了沒反應）
const summary = ref<SummaryItem[]>([]);
const trigger = ref(0);
const otherErrors = ref<Record<string, string>>({});

const next = () => {
  const items: SummaryItem[] = [];
  const total = groups.value.reduce((n, g) => n + listOf(g).length, 0);
  if (!total)
    items.push({ text: t('need.err.pickOne'), target: `need-choice-${activeGroup.value?.id}` });
  otherErrors.value = {};
  for (const g of groups.value) {
    if (listOf(g).includes('其他') && !otherOf(g).trim()) {
      otherErrors.value[g.id] = t('need.err.other');
      items.push({
        text: t('need.err.otherIn', { title: groupTitle(g) }),
        target: `need-other-${g.id}`
      });
    }
  }
  // 錯誤在另一個分頁時切過去，免得按了下一步卻看不到原因
  const bad = groups.value.findIndex((g) => otherErrors.value[g.id]);
  if (bad >= 0) activeTab.value = bad;
  summary.value = items;
  trigger.value++;
  if (items.length) return;
  flow.goNext();
};
</script>

<template>
  <AStepPage
    :title="serviceShortTitle(flow.service.value)"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <ErrorSummary :errors="summary" :trigger="trigger" />
    <ServiceTabs
      v-if="groups.length > 1"
      v-model="activeTab"
      :tab-list="tabs"
      id-prefix="need"
      :list-label="t('need.tabsLabel')"
    >
      <template #icon="{ item }">
        <AIcon :name="item.id === 'repair' ? 'repair' : 'assess'" class="h-5 w-5" />
      </template>
    </ServiceTabs>
    <div
      v-if="activeGroup"
      :key="activeGroup.id"
      id="need-panel"
      role="tabpanel"
      :aria-labelledby="groups.length > 1 ? `need-tab-${activeTab}` : undefined"
      :aria-label="groups.length > 1 ? undefined : groupTitle(activeGroup)"
    >
      <ASection :title="groups.length > 1 ? undefined : groupTitle(activeGroup)">
        <p class="text-base" :lang="zhAttr">{{ activeGroup.intro }}</p>
        <div
          v-if="activeGroup.notice"
          class="mt-3 flex gap-2 rounded-lg bg-red-50 p-3 text-red-700"
        >
          <AIcon name="info" class="mt-0.5 h-5 w-5 shrink-0" />
          <!-- 官方公告文字照原文；其中的電話不在號碼中間斷行，點了可以直接撥打 -->
          <p class="text-base font-semibold" :lang="zhAttr">
            <template v-for="(part, i) in phoneParts(activeGroup.notice)" :key="i">
              <button
                v-if="i % 2"
                type="button"
                class="a11y-focus whitespace-nowrap underline"
                @click="native.callPhone(part)"
              >
                {{ part }}
              </button>
              <template v-else>{{ part }}</template>
            </template>
          </p>
        </div>
        <div class="mt-4">
          <AChoice
            :model-value="listOf(activeGroup)"
            multiple
            :field-id="`need-choice-${activeGroup.id}`"
            :legend="groupTitle(activeGroup)"
            hide-legend
            :options="optionsOf(activeGroup)"
            @update:model-value="
              (v) => {
                setList(activeGroup!, v as string[]);
                summary = [];
              }
            "
          />
          <div v-if="listOf(activeGroup).includes('其他')" class="mt-4">
            <AInput
              :model-value="otherOf(activeGroup)"
              :label="tx('其他')"
              :field-id="`need-other-${activeGroup.id}`"
              required
              :error="otherErrors[activeGroup.id]"
              @update:model-value="(v) => setOther(activeGroup!, v)"
            />
          </div>
        </div>
      </ASection>
    </div>

    <template #footer>
      <BaseButton class="w-full !py-4" @click="next">{{ t('common.next') }}</BaseButton>
    </template>
  </AStepPage>
</template>
