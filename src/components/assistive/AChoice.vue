<script setup lang="ts">
import { computed } from 'vue';
import { uid } from '@/utils/assistive/uid';
import { t } from '@/i18n/assistive';
import AErrorText from './AErrorText.vue';
import AImage from './AImage.vue';
import AIcon, { type IconName } from './AIcon.vue';

export interface ChoiceOption {
  value: string;
  label: string;
  description?: string;
  /** 縮圖（照片）網址；載入失敗就不顯示 */
  image?: string;
  /** 沒有官方照片時的線條圖示，只裝飾，文字仍是主要資訊 */
  icon?: IconName;
  disabled?: boolean;
  /** 這個選項的文字是另一種語言（例如英文介面下的官方中文原文）時的 lang 屬性 */
  lang?: string;
}

const props = defineProps<{
  /** 指定欄位群組的 id（錯誤摘要連結用） */
  fieldId?: string;
  modelValue: string | string[];
  options: ChoiceOption[];
  legend: string;
  /** 複選用 checkbox，單選用 radio */
  multiple?: boolean;
  hint?: string;
  error?: string;
  required?: boolean;
  /** 讓 legend 只給讀屏使用（頁面標題已經是同一句話時） */
  hideLegend?: boolean;
}>();
const emit = defineEmits<{ 'update:modelValue': [string | string[]] }>();

const name = uid('choice');
const errorId = `${name}-error`;
const hintId = `${name}-hint`;
const describedby = computed(
  () => [props.hint && hintId, props.error && errorId].filter(Boolean).join(' ') || undefined
);

const isChecked = (value: string) =>
  props.multiple ? (props.modelValue as string[]).includes(value) : props.modelValue === value;

const onChange = (value: string, checked: boolean) => {
  if (!props.multiple) return emit('update:modelValue', value);
  const current = props.modelValue as string[];
  emit('update:modelValue', checked ? [...current, value] : current.filter((v) => v !== value));
};
</script>

<template>
  <!-- 單選用 radiogroup（aria-required／aria-invalid 只對它有效）；複選只用 aria-describedby 串到錯誤訊息 -->
  <fieldset
    :id="fieldId"
    class="min-w-0"
    :role="multiple ? undefined : 'radiogroup'"
    :aria-describedby="describedby"
    :aria-required="!multiple && required ? 'true' : undefined"
    :aria-invalid="!multiple && error ? 'true' : undefined"
  >
    <legend class="tp-h3-semibold mb-1" :class="{ 'sr-only': hideLegend }">
      {{ legend }}
      <span v-if="required && !hideLegend" class="text-red-500" aria-hidden="true">*</span>
      <span v-if="required" class="sr-only">{{ t('form.required') }}</span>
    </legend>
    <p v-if="hint" :id="hintId" class="mb-2 text-sm text-grey-700">{{ hint }}</p>
    <div class="flex flex-col gap-2" :class="{ 'mt-2': !hint && !hideLegend }">
      <label
        v-for="(o, i) in options"
        :key="o.value"
        class="a-rise relative flex min-h-14 cursor-pointer gap-3 rounded-lg border bg-white px-4 py-3"
        :style="{ '--i': Math.min(i, 8) }"
        :class="[
          o.image || o.icon ? 'items-center' : 'items-start',
          o.disabled
            ? 'cursor-not-allowed border-grey-100 bg-grey-50'
            : isChecked(o.value)
              ? 'border-primary-600 bg-primary-50'
              : 'border-grey-200',
          'has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-primary-600'
        ]"
      >
        <input
          class="peer sr-only"
          :type="multiple ? 'checkbox' : 'radio'"
          :name="name"
          :value="o.value"
          :checked="isChecked(o.value)"
          :disabled="o.disabled"
          @change="onChange(o.value, ($event.target as HTMLInputElement).checked)"
        />
        <!-- 自訂勾選樣式：以形狀（圓點／勾號）表示選取，不單靠顏色 -->
        <span
          class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center border-2"
          :class="[
            multiple ? 'rounded' : 'rounded-full',
            o.disabled
              ? 'border-grey-300 bg-grey-100'
              : isChecked(o.value)
                ? 'border-primary-600 bg-primary-600'
                : 'border-grey-500 bg-white'
          ]"
          aria-hidden="true"
        >
          <svg
            v-if="isChecked(o.value) && multiple"
            class="h-4 w-4 text-white"
            viewBox="0 0 16 16"
            fill="none"
          >
            <path
              d="M3 8.5l3.2 3L13 4.5"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <span v-else-if="isChecked(o.value)" class="h-2.5 w-2.5 rounded-full bg-white" />
        </span>
        <span class="flex-1">
          <span
            :lang="o.lang"
            class="block text-base"
            :class="[{ 'font-semibold': isChecked(o.value) }, o.disabled ? 'text-grey-700' : '']"
          >
            {{ o.label }}
          </span>
          <span v-if="o.description" class="mt-0.5 block whitespace-pre-line text-sm text-grey-700">
            {{ o.description }}
          </span>
        </span>
        <AImage
          v-if="o.image"
          :src="o.image"
          hide-on-error
          class="a-choice-tile h-[64px] w-[64px] shrink-0 rounded"
        />
        <span
          v-else-if="o.icon"
          class="a-choice-tile flex h-[64px] w-[64px] shrink-0 items-center justify-center rounded text-primary-700"
          :class="isChecked(o.value) ? 'bg-primary-100' : 'bg-primary-50'"
          aria-hidden="true"
        >
          <AIcon :name="o.icon" class="h-[32px] w-[32px]" />
        </span>
      </label>
    </div>
    <AErrorText v-if="error" :id="errorId">{{ error }}</AErrorText>
  </fieldset>
</template>
