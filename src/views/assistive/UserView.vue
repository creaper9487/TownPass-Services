<script setup lang="ts">
import { reactive, ref } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AInput from '@/components/assistive/AInput.vue';
import ASelect from '@/components/assistive/ASelect.vue';
import ATextarea from '@/components/assistive/ATextarea.vue';
import ErrorSummary from '@/components/assistive/ErrorSummary.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import { t } from '@/i18n/assistive';
import { taipeiDistricts } from '@/utils/assistive/centers';
import { isEmail, isTwId, toSummary, type SummaryItem } from '@/utils/assistive/validators';

// 官方表單「輔具使用者資料」：姓名（同聯絡人）、身分證字號、戶籍地行政區、居住地行政區、E-mail、備註。
const store = useAssistiveStore();
const flow = useAssistiveFlow();
const u = store.user;
const f = store.applicant;

// 不自動帶入聯絡人資料：照顧者代為預約時，使用者不是聯絡人本人。是本人時按「同聯絡人」。

const errors = reactive({ name: '', idNo: '', registered: '', email: '' });
const summary = ref<SummaryItem[]>([]);
const trigger = ref(0);

const validate = () => {
  errors.name = u.name.trim() ? '' : t('form.err.name');
  errors.idNo = !u.idNo.trim() ? t('user.err.idRequired') : isTwId(u.idNo) ? '' : t('user.err.id');
  errors.registered = u.registeredDistrict ? '' : t('user.err.registered');
  errors.email = f.email.trim() && !isEmail(f.email) ? t('form.err.email') : '';
  return toSummary(errors, 'user');
};
const onIdBlur = () => {
  if (u.idNo.trim()) errors.idNo = isTwId(u.idNo) ? '' : t('user.err.id');
};

const next = () => {
  summary.value = validate();
  trigger.value++;
  if (summary.value.length) return;
  flow.goNext();
};
</script>

<template>
  <AStepPage
    :title="t('user.title')"
    :lead="t('common.requiredNote')"
    :step="flow.current.value"
    :total="flow.total.value"
  >
    <ErrorSummary :errors="summary" :trigger="trigger" />
    <!-- 頁面標題已是「輔具使用者資料」，區塊不再重複同一個標題 -->
    <ASection>
      <div class="flex flex-col gap-5">
        <div>
          <AInput
            v-model="u.name"
            :label="t('form.name')"
            required
            autocomplete="off"
            field-id="user-name"
            :error="errors.name"
          />
          <BaseButton outline class="mt-2" @click="store.fillUserFromContact()">
            {{ t('user.sameAsContact') }}
          </BaseButton>
        </div>
        <AInput
          v-model="u.idNo"
          :label="t('form.idNo')"
          required
          uppercase
          :maxlength="10"
          autocomplete="off"
          field-id="user-idNo"
          :error="errors.idNo"
          @blur="onIdBlur"
        />
        <ASelect
          v-model="u.registeredDistrict"
          :label="t('user.registeredDistrict')"
          required
          :placeholder="t('form.choose')"
          :options="taipeiDistricts"
          field-id="user-registered"
          :error="errors.registered"
        />
        <ASelect
          v-model="u.livingDistrict"
          :label="t('user.livingDistrict')"
          :placeholder="t('form.choose')"
          :options="taipeiDistricts"
          field-id="user-livingDistrict"
        />
        <AInput
          v-model="f.email"
          :label="t('form.email')"
          type="email"
          inputmode="email"
          autocomplete="email"
          :hint="t('form.emailHint')"
          field-id="user-email"
          :error="errors.email"
        />
        <ATextarea v-model="u.remark" :label="t('form.remark')" field-id="user-remark" />
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
