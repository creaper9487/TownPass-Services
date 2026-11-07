<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { useAssistiveWelfareStore } from '@/stores/assistiveWelfare';
import { centerName, centers } from '@/utils/assistive/centers';
import { OFFICIAL_SITE, eligibleItems, type WelfareItem } from '@/utils/assistive/welfare';
import { t, tx, zhAttr } from '@/i18n/assistive';

const router = useRouter();
const native = useAssistiveNative();
const store = useAssistiveWelfareStore();

// 照官方問答結果：只列出這次答案可能符合的項目
const items = computed(() => eligibleItems(store.answers, store.age));

const open = (item: WelfareItem) => {
  if (item.page) router.push({ name: 'assistive-welfare-page', params: { slug: item.page } });
  else if (item.href)
    native.openLink(item.href.startsWith('/') ? OFFICIAL_SITE + item.href : item.href);
};
</script>

<template>
  <AStepPage :title="t('welfare.result.title')">
    <ASection v-if="items.length">
      <p class="text-base">{{ t('welfare.result.lead') }}</p>
      <ul class="mt-4 divide-y divide-grey-100">
        <li
          v-for="(item, i) in items"
          :key="item.title"
          class="a-rise"
          :style="{ '--i': Math.min(i, 10) }"
        >
          <button
            type="button"
            class="a11y-focus flex min-h-14 w-full items-center justify-between gap-3 py-3 text-left text-base"
            @click="open(item)"
          >
            <span class="font-semibold" :lang="zhAttr">{{ item.title }}</span>
            <img src="@/assets/images/down-icon.svg" alt="" class="h-6 w-6 shrink-0 -rotate-90" />
          </button>
        </li>
      </ul>
    </ASection>
    <ASection v-else>
      <div class="flex flex-col items-center py-6 text-center">
        <img src="@/assets/images/illustrations_no_data.svg" alt="" class="h-32" />
        <p class="mt-4 text-balance tp-h3-semibold">{{ t('welfare.result.empty.title') }}</p>
        <p class="mt-1 text-balance text-sm text-grey-700">{{ t('welfare.result.empty.hint') }}</p>
      </div>
      <ul class="flex flex-col gap-3">
        <li
          v-for="c in centers"
          :key="c.id"
          class="rounded-lg border border-grey-200 p-3 text-base"
        >
          <p class="font-semibold">{{ centerName(c) }}</p>
          <p class="mt-1 text-sm text-grey-700">
            {{ c.districts.map(tx).join(t('welfare.result.sep')) }}
          </p>
          <!-- 電話可以直接撥打，也不在號碼中間斷行 -->
          <button
            type="button"
            class="a11y-focus -my-1 flex min-h-11 items-center whitespace-nowrap font-semibold text-primary-700 underline"
            @click="native.callPhone(c.phone)"
          >
            {{ c.phone }}
          </button>
        </li>
      </ul>
    </ASection>
    <template #footer>
      <BaseButton outline class="w-full" link :route-info="{ name: 'assistive-welfare' }">
        {{ t('welfare.restart') }}
      </BaseButton>
    </template>
  </AStepPage>
</template>
