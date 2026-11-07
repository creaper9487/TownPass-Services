<script setup lang="ts">
import { nextTick, ref, watch } from 'vue';
import type { SummaryItem } from '@/utils/assistive/validators';

const props = defineProps<{ errors: SummaryItem[]; trigger: number }>();
const box = ref<HTMLElement>();

// 送出失敗時把焦點移到摘要，讀屏會唸出「有 N 個欄位需要修正」與清單；每一項都是連結，點了會跳到對應欄位。
watch(
  () => props.trigger,
  async () => {
    if (!props.errors.length) return;
    await nextTick();
    box.value?.focus();
    box.value?.scrollIntoView({ block: 'center' });
  }
);

const goTo = (id: string) => {
  const el = document.getElementById(id);
  if (!el) return;
  const target = el.matches('input,select,textarea,button')
    ? el
    : el.querySelector<HTMLElement>('input,select,textarea');
  target?.focus();
  target?.scrollIntoView({ block: 'center' });
};
</script>

<template>
  <div
    v-if="errors.length"
    ref="box"
    tabindex="-1"
    role="alert"
    class="mx-4 mt-4 rounded-lg border border-red-500 bg-red-50 p-4 text-sm text-grey-800 outline-none"
  >
    <p class="font-semibold text-red-700">有 {{ errors.length }} 個欄位需要修正</p>
    <ul class="mt-1 list-disc pl-5">
      <li v-for="e in errors" :key="e.target">
        <a
          :href="`#${e.target}`"
          class="a11y-focus inline-block min-h-6 underline"
          @click.prevent="goTo(e.target)"
        >
          {{ e.text }}
        </a>
      </li>
    </ul>
  </div>
</template>
