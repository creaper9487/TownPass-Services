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
import { t, tx } from '@/i18n/assistive';
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

const mobileMsg = () => t('contact.err.mobile');
const phoneMsg = () => t('contact.err.phone');

const validate = () => {
  errors.name = f.name.trim() ? '' : t('form.err.name');
  errors.mobile = !f.mobile.trim()
    ? t('contact.err.mobileRequired')
    : isMobile(f.mobile)
      ? ''
      : mobileMsg();
  // 官方：評估、維修、回收的電話是必填；借用只在有填時檢查格式
  errors.phone =
    !f.phone.trim() && !isBorrow.value
      ? t('contact.err.phoneRequired')
      : f.phone.trim() && !isLandline(f.phone)
        ? phoneMsg()
        : '';
  errors.gender = !isBorrow.value && !f.gender ? t('contact.err.gender') : '';
  errors.email = f.email.trim() && !isEmail(f.email) ? t('form.err.email') : '';
  return toSummary(errors, 'contact');
};
// 離開欄位時只檢查「已經填了但格式不對」的情況；必填的提醒留到按下一步。
const onBlur = (key: 'mobile' | 'phone' | 'email') => {
  if (key === 'mobile' && f.mobile.trim()) errors.mobile = isMobile(f.mobile) ? '' : mobileMsg();
  if (key === 'phone' && f.phone.trim()) errors.phone = isLandline(f.phone) ? '' : phoneMsg();
  if (key === 'email' && f.email.trim()) errors.email = isEmail(f.email) ? '' : t('form.err.email');
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
    :title="t('contact.title')"
    :lead="t('common.requiredNote')"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <p
      v-if="fromAccount"
      role="status"
      class="mx-4 mt-4 rounded-lg bg-primary-50 p-3 text-sm text-primary-800"
    >
      {{ t('contact.fromAccount') }}
    </p>
    <ErrorSummary :errors="summary" :trigger="trigger" />

    <ASection :title="t('contact.title')">
      <div class="flex flex-col gap-5">
        <AInput
          v-model="f.name"
          :label="t('form.name')"
          required
          autocomplete="name"
          field-id="contact-name"
          :error="errors.name"
        />
        <AInput
          v-model="f.phone"
          :label="t('form.phone')"
          :required="!isBorrow"
          type="tel"
          inputmode="tel"
          autocomplete="tel-national"
          :hint="t('contact.phoneHint')"
          field-id="contact-phone"
          :error="errors.phone"
          @blur="onBlur('phone')"
        />
        <AInput
          v-model="f.mobile"
          :label="t('form.mobile')"
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
          :legend="t('form.gender')"
          required
          field-id="contact-gender"
          :error="errors.gender"
          :options="[
            { value: 'M', label: tx('男') },
            { value: 'F', label: tx('女') }
          ]"
          @update:model-value="f.gender = $event as 'M' | 'F'"
        />
        <AInput
          v-if="isBorrow"
          v-model="f.email"
          :label="t('form.email')"
          type="email"
          inputmode="email"
          autocomplete="email"
          :hint="t('form.emailHint')"
          field-id="contact-email"
          :error="errors.email"
          @blur="onBlur('email')"
        />
      </div>
    </ASection>

    <template #footer>
      <div class="grid grid-cols-2 gap-2">
        <BaseButton outline @click="flow.goPrev()">{{ t('common.prev') }}</BaseButton>
        <BaseButton @click="next">{{ t('common.next') }}</BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
