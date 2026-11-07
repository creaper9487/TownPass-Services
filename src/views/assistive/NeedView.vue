<script setup lang="ts">
import { computed, ref } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AChoice from '@/components/assistive/AChoice.vue';
import AInput from '@/components/assistive/AInput.vue';
import AErrorText from '@/components/assistive/AErrorText.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import { services, type NeedGroup } from '@/utils/assistive/services';

// 官方表單：申請評估、申請維修（同一張表）／申請回收。說明與勾選項名稱照官方原文。
const store = useAssistiveStore();
const flow = useAssistiveFlow();
const groups = computed(() => services[flow.service.value].groups ?? []);

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
const optionsOf = (g: NeedGroup) => [
  ...g.options.map((o) => ({ value: o, label: o })),
  ...(g.other ? [{ value: '其他', label: '其他' }] : [])
];

const error = ref('');
const otherErrors = ref<Record<string, string>>({});

const next = () => {
  const total = groups.value.reduce((n, g) => n + listOf(g).length, 0);
  error.value = total ? '' : '請至少勾選一項';
  otherErrors.value = {};
  for (const g of groups.value) {
    if (listOf(g).includes('其他') && !otherOf(g).trim()) otherErrors.value[g.id] = '請填寫其他項目';
  }
  if (error.value || Object.keys(otherErrors.value).length) return;
  flow.goNext();
};
</script>

<template>
  <AStepPage
    :title="services[flow.service.value].shortTitle"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <ASection v-for="g in groups" :key="g.id" :title="g.title">
      <p class="text-base">{{ g.intro }}</p>
      <p v-if="g.notice" class="mt-3 text-base font-semibold text-red-600">{{ g.notice }}</p>
      <div class="mt-4">
        <AChoice
          :model-value="listOf(g)"
          multiple
          :legend="g.title"
          hide-legend
          :options="optionsOf(g)"
          @update:model-value="
            (v) => {
              setList(g, v as string[]);
              error = '';
            }
          "
        />
        <div v-if="listOf(g).includes('其他')" class="mt-4">
          <AInput
            :model-value="otherOf(g)"
            label="其他"
            required
            :error="otherErrors[g.id]"
            @update:model-value="(v) => setOther(g, v)"
          />
        </div>
      </div>
    </ASection>
    <ASection v-if="error">
      <AErrorText>{{ error }}</AErrorText>
    </ASection>

    <template #footer>
      <BaseButton class="w-full !py-4" @click="next">下一步</BaseButton>
    </template>
  </AStepPage>
</template>
