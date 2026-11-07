<script setup lang="ts">
import { useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveWelfareStore } from '@/stores/assistiveWelfare';
import { FIRST_QUESTION, welfare } from '@/utils/assistive/welfare';

const router = useRouter();
const store = useAssistiveWelfareStore();

const start = () => {
  store.reset();
  router.push({ name: 'assistive-welfare-question', params: { id: FIRST_QUESTION } });
};
</script>

<template>
  <AStepPage title="輔具福利查詢">
    <ASection :title="welfare.intro.title">
      <p class="text-base">{{ welfare.intro.text }}</p>
    </ASection>
    <template #footer>
      <BaseButton class="w-full" @click="start">{{ welfare.intro.button }}</BaseButton>
    </template>
  </AStepPage>
</template>
