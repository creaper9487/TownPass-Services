<script setup lang="ts">
import { useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import AIcon from '@/components/assistive/AIcon.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveWelfareStore } from '@/stores/assistiveWelfare';
import { FIRST_QUESTION } from '@/utils/assistive/welfare';
import { t } from '@/i18n/assistive';

const router = useRouter();
const store = useAssistiveWelfareStore();

const start = () => {
  store.reset();
  router.push({ name: 'assistive-welfare-question', params: { id: FIRST_QUESTION } });
};
</script>

<template>
  <AStepPage :title="t('welfare.title')">
    <!-- 內容很短：整塊置中並放一個圖示，不要讓文字貼在頂端、下面空一大片。圖示只裝飾，官方文字一字不改。 -->
    <section class="flex min-h-[60vh] flex-col items-center justify-center px-6 py-8 text-center">
      <span
        class="a-pop flex h-[96px] w-[96px] items-center justify-center rounded-full bg-primary-50 text-primary-700"
        aria-hidden="true"
      >
        <AIcon name="assess" class="h-[48px] w-[48px]" />
      </span>
      <h2 class="tp-h3-semibold mt-6 text-primary-700">{{ t('welfare.intro.title') }}</h2>
      <p class="mt-2 text-balance text-base">{{ t('welfare.introText') }}</p>
    </section>
    <template #footer>
      <BaseButton class="w-full" @click="start">{{ t('welfare.start') }}</BaseButton>
    </template>
  </AStepPage>
</template>
