<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AChoice from '@/components/assistive/AChoice.vue';
import AImage from '@/components/assistive/AImage.vue';
import AInput from '@/components/assistive/AInput.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveWelfareStore } from '@/stores/assistiveWelfare';
import { OFFICIAL_SITE, RESULT, checkAge, nextQuestion, welfare } from '@/utils/assistive/welfare';

const route = useRoute();
const router = useRouter();
const store = useAssistiveWelfareStore();

const id = computed(() => String(route.params.id));
const question = computed(() => welfare.questions[id.value]);
const prev = computed(() => store.previous(id.value));

const value = ref('');
const error = ref('');
// 同一個頁面元件在兩題之間切換時不會重新建立：換題就帶入這題先前的答案。
watch(
  id,
  () => {
    value.value = store.answers[id.value] ?? '';
    error.value = '';
  },
  { immediate: true }
);

/** 這題答完會不會直接看結果（按鈕要寫「觀看結果」） */
const toResult = computed(() => {
  if (!value.value || question.value.type === 'number') return false;
  return (
    nextQuestion(id.value, { ...store.answers, [id.value]: value.value }, store.age) === RESULT
  );
});

const next = () => {
  if (question.value.type === 'number') {
    error.value = checkAge(value.value);
  } else {
    error.value = value.value ? '' : '請選擇';
  }
  if (error.value) return;
  const target = store.answer(id.value, value.value.trim());
  if (target === RESULT) router.push({ name: 'assistive-welfare-result' });
  else router.push({ name: 'assistive-welfare-question', params: { id: target } });
};

const back = () => {
  if (prev.value) router.push({ name: 'assistive-welfare-question', params: { id: prev.value } });
};
</script>

<template>
  <AStepPage title="輔具福利查詢">
    <ASection>
      <p class="text-sm text-grey-700">問題{{ id }}</p>
      <h2 class="tp-h2 mt-1">{{ question.text }}</h2>
      <AImage
        v-if="question.image"
        :src="OFFICIAL_SITE + question.image"
        hide-on-error
        class="mt-4 h-28"
      />
      <div class="mt-5">
        <AInput
          v-if="question.type === 'number'"
          v-model="value"
          :label="question.text"
          hide-label
          required
          inputmode="numeric"
          :maxlength="3"
          field-id="welfare-answer"
          :error="error"
        />
        <AChoice
          v-else
          v-model="value"
          :legend="question.text"
          hide-legend
          field-id="welfare-answer"
          :error="error"
          :options="question.options"
        />
      </div>
    </ASection>
    <template #footer>
      <div class="grid gap-2" :class="prev ? 'grid-cols-2' : 'grid-cols-1'">
        <BaseButton v-if="prev" outline @click="back">上一題</BaseButton>
        <BaseButton @click="next">{{ toResult ? '觀看結果' : '下一題' }}</BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
