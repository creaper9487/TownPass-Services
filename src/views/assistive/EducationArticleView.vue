<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AVideoEmbed from '@/components/assistive/AVideoEmbed.vue';
import AEducationBody from '@/components/assistive/AEducationBody.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { t, tx, zhAttr } from '@/i18n/assistive';
import { articleById, parseBody, relatedOf } from '@/utils/assistive/education';

// 單篇衛教：標題、日期、影片（有的話放最前面，多數文章影片才是重點）、官網原文內文。
const route = useRoute();
const store = useAssistiveStore();
const article = computed(() => articleById(String(route.params.id)));
const blocks = computed(() => (article.value ? parseBody(article.value.lines) : []));
const related = computed(() => (article.value ? relatedOf(article.value) : null));

// 從衛教走到借用或評估，就是一次新的申辦：和首頁進入服務時一樣先重設進度
const start = () => store.begin(related.value?.key === 'assess' ? 'assess' : 'borrow');
</script>

<template>
  <AStepPage
    :title="article ? article.name : t('education.title')"
    :lead="article?.date"
    lead-lang="zh-TW"
  >
    <ASection v-if="!article">
      <p class="tp-h3-semibold">{{ t('education.notFound') }}</p>
      <BaseButton class="mt-4 w-full" link :route-info="{ name: 'assistive-education' }">
        {{ t('education.back') }}
      </BaseButton>
    </ASection>
    <template v-else>
      <ASection>
        <AVideoEmbed v-if="article.video" :id="article.video" :title="article.title" />
        <AEducationBody :blocks="blocks" :lang="zhAttr" :class="{ 'mt-6': article.video }" />
        <p class="mt-8 border-t border-grey-100 pt-3 text-sm text-grey-700">
          {{ t('education.source') }}
        </p>
      </ASection>
      <ASection v-if="related" :title="t('education.related.hint')">
        <RouterLink
          :to="related.to"
          class="a11y-focus base-button base-button--outline"
          @click="start"
        >
          {{
            t(`education.related.${related.key}`, {
              category: related.category ? tx(related.category) : ''
            })
          }}
        </RouterLink>
      </ASection>
    </template>
  </AStepPage>
</template>
