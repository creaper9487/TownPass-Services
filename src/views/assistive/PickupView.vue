<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AChoice from '@/components/assistive/AChoice.vue';
import AInput from '@/components/assistive/AInput.vue';
import ASelect from '@/components/assistive/ASelect.vue';
import ATextarea from '@/components/assistive/ATextarea.vue';
import ErrorSummary from '@/components/assistive/ErrorSummary.vue';
import { toSummary, type SummaryItem } from '@/utils/assistive/validators';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import { taipeiDistricts } from '@/utils/assistive/centers';

const store = useAssistiveStore();
const flow = useAssistiveFlow();
const p = store.pickup;

const errors = reactive({ district: '', address: '', elevator: '' });
const summary = ref<SummaryItem[]>([]);
const trigger = ref(0);

const certificate = computed<string[]>({
  get: () => (p.needCertificate ? ['yes'] : []),
  set: (v) => (p.needCertificate = v.includes('yes'))
});

const next = () => {
  errors.district = p.district ? '' : '請選擇輔具所在的行政區';
  errors.address = p.address.trim() ? '' : '請輸入輔具所在的地址';
  errors.elevator = p.hasElevator ? '' : '請選擇有沒有電梯';
  summary.value = toSummary(errors, 'pickup');
  trigger.value++;
  if (!summary.value.length) flow.goNext();
};
</script>

<template>
  <AStepPage
    title="輔具在哪裡？"
    lead="中心會到這個地址收取輔具。* 為必填。"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <ErrorSummary :errors="summary" :trigger="trigger" />
    <ASection title="收取地點">
      <div class="flex flex-col gap-5">
        <ASelect
          v-model="p.district"
          label="行政區"
          required
          placeholder="請選擇"
          :options="taipeiDistricts"
          field-id="pickup-district"
          :error="errors.district"
        />
        <AInput
          v-model="p.address"
          label="地址"
          required
          autocomplete="street-address"
          hint="路名、巷弄、門牌號碼與樓層"
          field-id="pickup-address"
          :error="errors.address"
        />
        <AChoice
          :model-value="p.hasElevator"
          legend="有沒有電梯？"
          required
          field-id="pickup-elevator"
          :error="errors.elevator"
          :options="[
            { value: 'yes', label: '有電梯' },
            { value: 'no', label: '沒有電梯' }
          ]"
          @update:model-value="p.hasElevator = $event as 'yes' | 'no'"
        />
        <p
          v-if="store.center"
          role="status"
          class="rounded-lg bg-primary-50 p-3 text-sm text-primary-800"
        >
          這個地區由 {{ store.center.name }} 負責。
        </p>
      </div>
    </ASection>
    <ASection title="其他">
      <div class="flex flex-col gap-5">
        <AChoice
          v-model="certificate"
          multiple
          legend="回收證明"
          hide-legend
          :options="[{ value: 'yes', label: '我需要回收證明' }]"
        />
        <ATextarea v-model="p.remark" label="備註" hint="例如輔具的狀況、方便聯絡的時段。" />
      </div>
    </ASection>
    <template #footer>
      <div class="grid grid-cols-2 gap-2">
        <BaseButton outline @click="flow.goPrev()">上一步</BaseButton>
        <BaseButton @click="next">下一步</BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
