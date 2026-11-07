<script setup lang="ts">
import { computed } from 'vue';
import { uid } from '@/utils/assistive/uid';
import AErrorText from './AErrorText.vue';

const props = defineProps<{
  /** 指定欄位 id（錯誤摘要連結用）；沒給就自動產生 */
  fieldId?: string;
  modelValue: string;
  label: string;
  type?: 'text' | 'tel' | 'email';
  inputmode?: 'text' | 'tel' | 'email' | 'numeric';
  autocomplete?: string;
  placeholder?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  maxlength?: number;
  uppercase?: boolean;
  /** 欄位上方已有同樣的標題時，只留給讀屏使用 */
  hideLabel?: boolean;
}>();
const emit = defineEmits<{ 'update:modelValue': [string]; blur: [] }>();

const id = props.fieldId ?? uid('field');
const hintId = `${id}-hint`;
const errorId = `${id}-error`;
const describedby = computed(
  () => [props.hint && hintId, props.error && errorId].filter(Boolean).join(' ') || undefined
);

const onInput = (e: Event) => {
  const value = (e.target as HTMLInputElement).value;
  emit('update:modelValue', props.uppercase ? value.toUpperCase() : value);
};
</script>

<template>
  <div>
    <label :for="id" :class="hideLabel ? 'sr-only' : 'tp-h3-semibold mb-1 block'">
      {{ label }}
      <span v-if="required" class="text-red-500" aria-hidden="true">*</span>
      <span v-else-if="!hideLabel" class="ml-1 text-sm font-normal text-grey-700">（選填）</span>
    </label>
    <p v-if="hint" :id="hintId" class="mb-2 text-sm text-grey-700">{{ hint }}</p>
    <input
      :id="id"
      :value="modelValue"
      :type="type ?? 'text'"
      :inputmode="inputmode"
      :autocomplete="autocomplete"
      :placeholder="placeholder"
      :maxlength="maxlength"
      :required="required"
      :aria-required="required || undefined"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="describedby"
      class="min-h-12 w-full rounded-lg bg-grey-50 px-3 text-base placeholder:text-grey-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
      :class="{ 'ring-1 ring-red-600': error }"
      @input="onInput"
      @blur="emit('blur')"
    />
    <AErrorText v-if="error" :id="errorId">{{ error }}</AErrorText>
  </div>
</template>
