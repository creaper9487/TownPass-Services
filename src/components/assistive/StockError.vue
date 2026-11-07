<script setup lang="ts">
import BaseButton from '@/components/atoms/BaseButton.vue';

defineEmits<{ retry: [] }>();
</script>

<template>
  <div role="alert" class="rounded-lg border border-red-500 bg-red-50 p-4">
    <p class="tp-h3-semibold text-red-700">暫時讀不到庫存</p>
    <p class="mt-1 text-sm text-grey-800">請檢查網路後再試一次。</p>
    <BaseButton class="mt-3 w-full" @click="$emit('retry')">重新載入</BaseButton>
  </div>
</template>
