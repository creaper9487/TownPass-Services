<script setup lang="ts">
import AIcon, { type IconName } from './AIcon.vue';

// 「接下來」這類步驟清單的一列：左邊圖示，右邊是文字。列與列之間用細線連起來，表示先後順序。
// 圖示只裝飾；清單本身是 <ol>，讀屏仍然會唸出「第幾項，共幾項」。
defineProps<{ icon: IconName }>();
</script>

<template>
  <li
    class="relative flex gap-[12px] before:absolute before:bottom-[-1.25rem] before:left-[20px] before:top-[44px] before:w-px before:bg-primary-200 last:before:hidden"
  >
    <span
      class="flex h-[40px] w-[40px] shrink-0 items-center justify-center rounded-full bg-primary-50 text-primary-700"
      aria-hidden="true"
    >
      <AIcon :name="icon" class="h-[24px] w-[24px]" />
    </span>
    <div class="min-w-0 flex-1 pt-1.5 text-base"><slot /></div>
  </li>
</template>
