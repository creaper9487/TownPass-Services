<script setup lang="ts">
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow, stepRoute } from '@/composables/useAssistiveFlow';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AImage from '@/components/assistive/AImage.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';

// 官方「本次預約項目」：可以一次借好幾件，再一起選中心。
const store = useAssistiveStore();
const flow = useAssistiveFlow();

const label = (v: { categoryName: string; name: string; spec: string }) =>
  [v.categoryName, v.name, v.spec].filter((x) => x && x !== '---' && x !== '--').join('・');
</script>

<template>
  <AStepPage title="本次預約項目" :step="flow.current.value" :total="flow.total.value">
    <ASection grey>
      <p v-if="!store.variants.length" class="text-base">尚未選擇輔具</p>
      <ul v-else class="flex flex-col gap-3">
        <li v-for="v in store.variants" :key="v.id" class="tp-card flex items-center gap-3 p-3">
          <AImage v-if="v.image" :src="v.image" hide-on-error class="h-16 w-16 shrink-0" />
          <p class="min-w-0 flex-1 break-words text-base font-semibold">{{ label(v) }}</p>
          <BaseButton outline class="shrink-0" @click="store.removeVariant(v.id)">
            刪除<span class="sr-only">：{{ label(v) }}</span>
          </BaseButton>
        </li>
      </ul>
    </ASection>

    <template #footer>
      <div class="grid grid-cols-2 gap-2">
        <BaseButton outline link :route-info="stepRoute('borrow', 'items')">
          繼續選擇輔具
        </BaseButton>
        <BaseButton :disabled="!store.variants.length" @click="flow.goNext()">下一步</BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
