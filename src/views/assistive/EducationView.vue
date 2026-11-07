<script setup lang="ts">
import { computed, ref } from 'vue';
import { RouterLink } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AIcon from '@/components/assistive/AIcon.vue';
import { t, zhAttr } from '@/i18n/assistive';
import { articles, educationCategories, excerptOf } from '@/utils/assistive/education';

// 官網「輔具衛教」：文章由新到舊。官網沒有分類，這裡依標題前綴【輔具介紹】【維修保養】【宣導影片】提供篩選。
const active = ref('');
const chips = computed(() => [
  { id: '', label: t('education.tab.all') },
  ...educationCategories.map((c) => ({ id: c, label: t(`education.tab.${c}`) }))
]);
const shown = computed(() =>
  active.value ? articles.filter((a) => a.category === active.value) : articles
);
const tagOf = (category: string) => (category ? t(`education.tab.${category}`) : '');
</script>

<template>
  <AStepPage :title="t('education.title')">
    <ASection>
      <div role="group" :aria-label="t('education.tabs')" class="flex flex-wrap gap-2">
        <button
          v-for="c in chips"
          :key="c.id"
          type="button"
          :aria-pressed="active === c.id"
          class="a11y-focus min-h-11 rounded-full border px-4 text-base"
          :class="
            active === c.id
              ? 'border-primary-700 bg-primary-700 font-semibold text-white'
              : 'border-grey-300 bg-white text-grey-800'
          "
          @click="active = c.id"
        >
          {{ c.label }}
        </button>
      </div>
      <p role="status" class="mt-3 text-sm text-grey-700">
        {{ t('education.count', { n: shown.length }) }}
      </p>
      <ul id="education-panel" class="mt-3 flex flex-col gap-3">
        <li v-for="(a, i) in shown" :key="a.id" class="a-rise" :style="{ '--i': Math.min(i, 8) }">
          <RouterLink
            :to="{ name: 'assistive-education-article', params: { id: a.id } }"
            class="a11y-focus tp-card block border border-grey-100 p-4"
          >
            <span v-if="a.category || a.video" class="flex flex-wrap items-center gap-2">
              <span v-if="a.category" class="tp-tag">{{ tagOf(a.category) }}</span>
              <span
                v-if="a.video"
                class="tp-tag inline-flex items-center gap-1 !border-grey-300 !text-grey-700"
              >
                <AIcon name="play" class="h-[14px] w-[14px] shrink-0" />
                {{ t('education.hasVideo') }}
              </span>
            </span>
            <span class="tp-h3-semibold mt-2 block break-words" :lang="zhAttr">{{ a.name }}</span>
            <span class="mt-1 block text-sm text-grey-700" :lang="zhAttr">{{ a.date }}</span>
            <span class="mt-2 line-clamp-2 block text-sm text-grey-700" :lang="zhAttr">
              {{ excerptOf(a) }}
            </span>
          </RouterLink>
        </li>
      </ul>
    </ASection>
  </AStepPage>
</template>
