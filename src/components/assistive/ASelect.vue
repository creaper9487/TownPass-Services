<script setup lang="ts">
import { computed } from 'vue';
import { uid } from '@/utils/assistive/uid';
import AErrorText from './AErrorText.vue';

const props = defineProps<{
  /** 指定欄位 id（錯誤摘要連結用）；沒給就自動產生 */
  fieldId?: string;
  modelValue: string;
  label: string;
  options: string[];
  placeholder?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  autocomplete?: string;
}>();
const emit = defineEmits<{ 'update:modelValue': [string] }>();

const id = props.fieldId ?? uid('select');
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
    <div class="relative">
      <select
        :id="id"
        :value="modelValue"
        :required="required"
        :aria-required="required || undefined"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describedby"
        :autocomplete="autocomplete"
        class="min-h-12 w-full appearance-none rounded-lg bg-grey-50 py-3 pl-3 pr-11 text-base focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
        :class="{ 'ring-1 ring-red-600': error, 'text-grey-600': !modelValue }"
        @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">{{ placeholder ?? '請選擇' }}</option>
        <option v-for="o in options" :key="o" :value="o" class="text-grey-800">{{ o }}</option>
      </select>
      <img
        src="@/assets/images/down-icon.svg"
        alt=""
        class="pointer-events-none absolute right-3 top-1/2 h-6 w-6 -translate-y-1/2"
      />
    </div>
    <AErrorText v-if="error" :id="errorId">{{ error }}</AErrorText>
  </div>
</template>
