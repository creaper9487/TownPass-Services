<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AChoice from '@/components/assistive/AChoice.vue';
import AInput from '@/components/assistive/AInput.vue';
import ErrorSummary from '@/components/assistive/ErrorSummary.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import {
  isEmail,
  isLandline,
  isMobile,
  toSummary,
  type SummaryItem
} from '@/utils/assistive/validators';

// 官方表單「聯絡人資料」：姓名、電話（將以此欄位進行預約查詢）、手機、性別。
const store = useAssistiveStore();
const flow = useAssistiveFlow();
const f = store.applicant;

store.applyAccount();

const isBorrow = computed(() => flow.service.value === 'borrow');
const errors = reactive({ name: '', mobile: '', phone: '', gender: '', email: '' });
const trigger = ref(0);
const fromAccount = computed(
  () => !!store.account && (f.name === store.account.name || f.mobile === store.account.mobile)
);

const MOBILE_MSG = '手機要 10 碼、09 開頭，例如 0912345678';
const PHONE_MSG = '電話請含區碼，例如 0224597892';

const validate = () => {
  errors.name = f.name.trim() ? '' : '請輸入姓名';
  errors.mobile = !f.mobile.trim() ? '請輸入手機' : isMobile(f.mobile) ? '' : MOBILE_MSG;
  // 官方：評估、維修、回收的電話是必填；借用只在有填時檢查格式
  errors.phone =
    !f.phone.trim() && !isBorrow.value
      ? '請輸入電話'
      : f.phone.trim() && !isLandline(f.phone)
        ? PHONE_MSG
        : '';
  errors.gender = !isBorrow.value && !f.gender ? '請選擇性別' : '';
  errors.email = f.email.trim() && !isEmail(f.email) ? 'E-mail 格式不正確' : '';
  return toSummary(errors, 'contact');
};
// 離開欄位時只檢查「已經填了但格式不對」的情況；必填的提醒留到按下一步。
const onBlur = (key: 'mobile' | 'phone' | 'email') => {
  if (key === 'mobile' && f.mobile.trim()) errors.mobile = isMobile(f.mobile) ? '' : MOBILE_MSG;
  if (key === 'phone' && f.phone.trim()) errors.phone = isLandline(f.phone) ? '' : PHONE_MSG;
  if (key === 'email' && f.email.trim()) errors.email = isEmail(f.email) ? '' : 'E-mail 格式不正確';
};
const summary = ref<SummaryItem[]>([]);

const next = () => {
  summary.value = validate();
  trigger.value++;
  if (summary.value.length) return;
  flow.goNext();
};
</script>

<template>
  <AStepPage
    title="聯絡人資料"
    lead="*表示為必填欄位"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <p
      v-if="fromAccount"
      role="status"
      class="mx-4 mt-4 rounded-lg bg-primary-50 p-3 text-sm text-primary-800"
    >
      已帶入台北通資料
    </p>
    <ErrorSummary :errors="summary" :trigger="trigger" />

    <ASection title="聯絡人資料">
      <div class="flex flex-col gap-5">
        <AInput
          v-model="f.name"
          label="姓名"
          required
          autocomplete="name"
          field-id="contact-name"
          :error="errors.name"
        />
        <AInput
          v-model="f.phone"
          label="電話"
          :required="!isBorrow"
          type="tel"
          inputmode="tel"
          autocomplete="tel-national"
          hint="ex:0224597892 (將以此欄位進行預約查詢)"
          field-id="contact-phone"
          :error="errors.phone"
          @blur="onBlur('phone')"
        />
        <AInput
          v-model="f.mobile"
          label="手機"
          required
          type="tel"
          inputmode="tel"
          autocomplete="tel"
          field-id="contact-mobile"
          :error="errors.mobile"
          @blur="onBlur('mobile')"
        />
        <AChoice
          v-if="!isBorrow"
          :model-value="f.gender"
          legend="性別"
          required
          field-id="contact-gender"
          :error="errors.gender"
          :options="[
            { value: 'M', label: '男' },
            { value: 'F', label: '女' }
          ]"
          @update:model-value="f.gender = $event as 'M' | 'F'"
        />
        <AInput
          v-if="isBorrow"
          v-model="f.email"
          label="E-mail"
          type="email"
          inputmode="email"
          autocomplete="email"
          hint="將以此email寄送預約單"
          field-id="contact-email"
          :error="errors.email"
          @blur="onBlur('email')"
        />
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
