<script setup lang="ts">
import { ref } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AChoice from '@/components/assistive/AChoice.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import { officialCenterRows } from '@/utils/assistive/centers';
import { BORROW_RULES } from '@/utils/assistive/services';

// 官方「二手輔具借用須知」：原文照登，三項同意都勾選後按「我同意」。
const store = useAssistiveStore();
const flow = useAssistiveFlow();

const checked = ref(BORROW_RULES.consents.filter((_, i) => store.consents[i]));
const error = ref('');

const agree = () => {
  store.consents = BORROW_RULES.consents.map((a) => checked.value.includes(a));
  if (!store.consents.every(Boolean)) {
    error.value = '請勾選以上三項注意事項。';
    return;
  }
  flow.goNext();
};
</script>

<template>
  <AStepPage :title="BORROW_RULES.title" :step="flow.current.value" :total="flow.total.value">
    <ASection>
      <dl class="flex flex-col gap-3 text-base">
        <div v-for="[k, v] in BORROW_RULES.items" :key="k">
          <dt v-if="!v" class="tp-h3-semibold mt-2">{{ k }}</dt>
          <template v-else>
            <dt class="inline font-semibold">{{ k }}</dt>
            <dd class="inline">{{ v }}</dd>
          </template>
        </div>
      </dl>
      <p class="mt-4 text-sm text-grey-700">{{ BORROW_RULES.footnote }}</p>
    </ASection>

    <ASection title="中心名稱、開放時間、中心地址、中心電話">
      <ul class="flex flex-col gap-3">
        <li v-for="c in officialCenterRows" :key="c.name" class="rounded-lg border border-grey-200 p-3 text-base">
          <p class="font-semibold">{{ c.name }}</p>
          <p class="mt-1">{{ c.hours }}</p>
          <p>{{ c.address }}</p>
          <p>{{ c.phone }}</p>
        </li>
      </ul>
    </ASection>

    <ASection>
      <AChoice
        v-model="checked"
        multiple
        required
        :legend="BORROW_RULES.consentIntro"
        :hint="BORROW_RULES.consentNote"
        :error="error"
        :options="BORROW_RULES.consents.map((a) => ({ value: a, label: a }))"
        @update:model-value="error = ''"
      />
    </ASection>

    <template #footer>
      <div class="grid grid-cols-2 gap-2">
        <BaseButton outline link :route-info="{ name: 'assistive-home' }">我不同意</BaseButton>
        <BaseButton @click="agree">我同意</BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
