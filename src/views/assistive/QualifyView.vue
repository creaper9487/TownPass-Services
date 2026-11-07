<script setup lang="ts">
import { computed } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { GATE_QUESTION, NOT_TAIPEI_NOTICE, services } from '@/utils/assistive/services';

// 官方「選擇戶籍地」：問一句「請問您的戶籍地是否在臺北市?」，點選就直接進下一頁，沒有下一步按鈕。
const store = useAssistiveStore();
const flow = useAssistiveFlow();
const native = useAssistiveNative();

const gateTitle = computed(() => services[flow.service.value].gateTitle);

const choose = (inTaipei: boolean) => {
  store.qualified = inTaipei;
  if (inTaipei) flow.goNext();
};
</script>

<template>
  <AStepPage :title="gateTitle" :step="flow.current.value" :total="flow.total.value">
    <ASection>
      <p class="mb-4 text-base">{{ GATE_QUESTION }}</p>
      <div class="grid grid-cols-2 gap-3">
        <button
          type="button"
          class="a11y-focus flex min-h-28 items-center justify-center rounded-lg border-2 text-lg font-semibold"
          :class="
            store.qualified === true
              ? 'border-primary-700 bg-primary-700 text-white'
              : 'border-primary-700 bg-white text-primary-700'
          "
          @click="choose(true)"
        >
          臺北市
        </button>
        <button
          type="button"
          class="a11y-focus flex min-h-28 items-center justify-center rounded-lg border-2 text-lg font-semibold"
          :class="
            store.qualified === false
              ? 'border-primary-700 bg-primary-700 text-white'
              : 'border-primary-700 bg-white text-primary-700'
          "
          @click="choose(false)"
        >
          非臺北市
        </button>
      </div>

      <div v-if="store.qualified === false" role="status" class="mt-6">
        <h2 class="tp-h3-semibold">{{ NOT_TAIPEI_NOTICE.title }}</h2>
        <p class="mt-2 text-base">{{ NOT_TAIPEI_NOTICE.body }}</p>
        <BaseButton class="mt-4 w-full" @click="native.openLink(NOT_TAIPEI_NOTICE.link.url)">
          {{ NOT_TAIPEI_NOTICE.link.label }}
        </BaseButton>
      </div>
    </ASection>
  </AStepPage>
</template>
