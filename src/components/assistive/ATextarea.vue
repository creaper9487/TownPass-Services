<script setup lang="ts">
import { computed } from 'vue';
import { uid } from '@/utils/assistive/uid';
import AErrorText from './AErrorText.vue';

const props = defineProps<{
  /** 指定欄位 id（錯誤摘要連結用）；沒給就自動產生 */
  fieldId?: string;
  modelValue: string;
  label: string;
  placeholder?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  rows?: number;
  maxlength?: number;
}>();
const emit = defineEmits<{ 'update:modelValue': [string] }>();

const id = props.fieldId ?? uid('textarea');
const hintId = `${id}-hint`;
const errorId = `${id}-error`;
const describedby = computed(
  () => [props.hint && hintId, props.error && errorId].filter(Boolean).join(' ') || undefined
);
</script>

<template>
  <div>
    <label :for="id" class="tp-h3-semibold mb-1 block">
      {{ label }}
      <span v-if="required" class="text-red-500" aria-hidden="true">*</span>
      <span v-else class="ml-1 text-sm font-normal text-grey-700">（選填）</span>
    </label>
    <p v-if="hint" :id="hintId" class="mb-2 text-sm text-grey-700">{{ hint }}</p>
    <textarea
      :id="id"
      :value="modelValue"
      :rows="rows ?? 4"
      :maxlength="maxlength"
      :placeholder="placeholder"
      :required="required"
      :aria-required="required || undefined"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="describedby"
      class="w-full resize-y rounded-lg bg-grey-50 px-3 py-3 text-base placeholder:text-grey-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
      :class="{ 'ring-1 ring-red-600': error }"
      @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    />
    <AErrorText v-if="error" :id="errorId">{{ error }}</AErrorText>
  </div>
</template>
