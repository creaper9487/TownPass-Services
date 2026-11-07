<script setup lang="ts">
import { computed } from 'vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { t } from '@/i18n/assistive';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import type { EducationBlock } from '@/utils/assistive/education';

// 衛教文章的內文：標題、步驟、清單、聯絡中心。文字全部是官網原文，這裡只決定怎麼排。
const props = defineProps<{ blocks: EducationBlock[] }>();
const native = useAssistiveNative();

type Step = Extract<EducationBlock, { type: 'step' }>;
type Group = Exclude<EducationBlock, { type: 'step' }> | { type: 'steps'; steps: Step[] };

// 相鄰的步驟合成一個清單（讀屏會唸出「第幾步，共幾步」）
const groups = computed(() =>
  props.blocks.reduce<Group[]>((acc, b) => {
    if (b.type !== 'step') {
      acc.push(b);
      return acc;
    }
    const last = acc[acc.length - 1];
    if (last?.type === 'steps') last.steps.push(b);
    else acc.push({ type: 'steps', steps: [b] });
    return acc;
  }, [])
);
</script>

<template>
  <div class="flex flex-col gap-4 text-base leading-7 text-grey-800">
    <template v-for="(g, i) in groups" :key="i">
      <h2 v-if="g.type === 'h'" class="tp-h3-semibold mt-4 text-primary-700">{{ g.text }}</h2>
      <h3 v-else-if="g.type === 'sub'" class="mt-2 font-semibold">{{ g.text }}</h3>
      <p v-else-if="g.type === 'p'">{{ g.text }}</p>
      <ol v-else-if="g.type === 'steps'" role="list" class="flex flex-col gap-3">
        <li
          v-for="s in g.steps"
          :key="s.label"
          class="rounded-lg border border-primary-200 bg-primary-50 p-4"
        >
          <p class="tp-tag !bg-white font-semibold">{{ s.label }}</p>
          <p v-for="(l, k) in s.lines" :key="k" class="mt-2">{{ l }}</p>
        </li>
      </ol>
      <ul v-else-if="g.type === 'ul'" class="list-disc space-y-2 pl-6">
        <li v-for="(it, k) in g.items" :key="k">{{ it }}</li>
      </ul>
      <ol v-else-if="g.type === 'ol'" class="list-decimal space-y-2 pl-6">
        <li v-for="(it, k) in g.items" :key="k">{{ it }}</li>
      </ol>
      <div v-else-if="g.type === 'contact'" class="tp-card p-4">
        <p class="font-semibold">{{ g.name }}</p>
        <p class="mt-1 text-sm leading-6 text-grey-700">{{ g.display }}</p>
        <p v-if="g.address" class="text-sm leading-6 text-grey-700">{{ g.address }}</p>
        <BaseButton outline class="mt-3 w-full" @click="native.callPhone(g.phone)">
          {{ t('education.call') }}
          <span class="sr-only">{{ g.name }}</span>
        </BaseButton>
      </div>
    </template>
  </div>
</template>
