<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { welfare, type WelfareBlock } from '@/utils/assistive/welfare';
import { t, zhAttr } from '@/i18n/assistive';

const route = useRoute();
const native = useAssistiveNative();

const page = computed(() => welfare.pages[String(route.params.slug)]);

/** 連續的條列項目併成同一個清單（有序／無序分開） */
type Group =
  | { kind: 'h' | 'p' | 'link'; block: WelfareBlock }
  | { kind: 'list'; ordered: boolean; items: WelfareBlock[] };
const groups = computed(() => {
  const out: Group[] = [];
  for (const b of page.value?.blocks ?? []) {
    if (b.type === 'li') {
      const last = out[out.length - 1];
      if (last?.kind === 'list' && last.ordered === !!b.ordered) last.items.push(b);
      else out.push({ kind: 'list', ordered: !!b.ordered, items: [b] });
    } else out.push({ kind: b.type, block: b });
  }
  return out;
});
</script>

<template>
  <AStepPage :title="page?.title ?? t('welfare.title')">
    <ASection v-if="!page">
      <p class="tp-h3-semibold">{{ t('welfare.notFound') }}</p>
    </ASection>
    <ASection v-else>
      <div class="flex flex-col gap-3 text-base" :lang="zhAttr">
        <template v-for="(g, i) in groups" :key="i">
          <h2 v-if="g.kind === 'h'" class="tp-h3-semibold mt-3 text-primary-700">
            {{ g.block.text }}
          </h2>
          <p v-else-if="g.kind === 'p'">{{ g.block.text }}</p>
          <component
            :is="g.ordered ? 'ol' : 'ul'"
            v-else-if="g.kind === 'list'"
            class="space-y-2 pl-5"
            :class="g.ordered ? 'list-decimal' : 'list-disc'"
          >
            <li v-for="(it, j) in g.items" :key="j">{{ it.text }}</li>
          </component>
          <button
            v-else-if="g.kind === 'link' && g.block.href"
            type="button"
            class="a11y-focus min-h-11 text-left font-semibold text-primary-700 underline"
            @click="native.openLink(g.block.href)"
          >
            {{ g.block.text }}
          </button>
        </template>
      </div>
    </ASection>
  </AStepPage>
</template>
