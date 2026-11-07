<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AInput from '@/components/assistive/AInput.vue';
import ASelect from '@/components/assistive/ASelect.vue';
import ATextarea from '@/components/assistive/ATextarea.vue';
import ErrorSummary from '@/components/assistive/ErrorSummary.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import { counties, taipeiDistricts } from '@/utils/assistive/centers';
import { isEmail, isTwId, toSummary, type SummaryItem } from '@/utils/assistive/validators';

// 官方表單「輔具使用者資料」：姓名（同聯絡人）、身分證字號、戶籍地行政區、居住地行政區、E-mail、備註。
const store = useAssistiveStore();
const flow = useAssistiveFlow();
const u = store.user;
const f = store.applicant;

// 台北通帳號資料已授權時，先把聯絡人本人的資料帶進來（沒填過才帶）。
onMounted(() => {
  if (!u.name) store.fillUserFromContact();
});

const errors = reactive({ name: '', idNo: '', registered: '', email: '' });
const summary = ref<SummaryItem[]>([]);
const trigger = ref(0);

const validate = () => {
  errors.name = u.name.trim() ? '' : '請輸入姓名';
  errors.idNo = !u.idNo.trim()
    ? '請輸入身分證字號'
    : isTwId(u.idNo)
      ? ''
      : '身分證字號格式不正確，請再檢查一次';
  errors.registered = u.registeredDistrict ? '' : '請選擇戶籍地行政區';
  errors.email = f.email.trim() && !isEmail(f.email) ? 'E-mail 格式不正確' : '';
  return toSummary(errors, 'user');
};
const onIdBlur = () => {
  if (u.idNo.trim()) errors.idNo = isTwId(u.idNo) ? '' : '身分證字號格式不正確，請再檢查一次';
};

const next = () => {
  summary.value = validate();
  trigger.value++;
  if (summary.value.length) return;
  flow.goNext();
};
</script>

<template>
  <AStepPage title="輔具使用者資料" lead="*表示為必填欄位" :step="flow.current.value" :total="flow.total.value">
    <ErrorSummary :errors="summary" :trigger="trigger" />
    <ASection title="輔具使用者資料">
      <div class="flex flex-col gap-5">
        <div>
          <AInput
            v-model="u.name"
            label="姓名"
            required
            autocomplete="off"
            field-id="user-name"
            :error="errors.name"
          />
          <BaseButton outline class="mt-2" @click="store.fillUserFromContact()">同聯絡人</BaseButton>
        </div>
        <AInput
          v-model="u.idNo"
          label="身分證字號"
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
          label="戶籍地行政區"
          required
          placeholder="臺北市"
          :options="taipeiDistricts"
          field-id="user-registered"
          :error="errors.registered"
        />
        <ASelect v-model="u.livingCounty" label="居住地行政區" :options="counties" field-id="user-livingCounty" />
        <ASelect
          v-if="u.livingCounty === '臺北市'"
          v-model="u.livingDistrict"
          label="居住地行政區（區）"
          placeholder="--"
          :options="taipeiDistricts"
          field-id="user-livingDistrict"
        />
        <AInput
          v-model="f.email"
          label="E-mail"
          type="email"
          inputmode="email"
          autocomplete="email"
          hint="將以此email寄送預約單"
          field-id="user-email"
          :error="errors.email"
        />
        <ATextarea v-model="u.remark" label="備註" field-id="user-remark" />
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
