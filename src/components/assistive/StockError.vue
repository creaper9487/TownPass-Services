<script setup lang="ts">
import BaseButton from '@/components/atoms/BaseButton.vue';
import { t } from '@/i18n/assistive';

defineEmits<{ retry: [] }>();
</script>

<template>
  <div role="alert" class="rounded-lg border border-red-500 bg-red-50 p-4">
    <p class="tp-h3-semibold text-red-700">{{ t('stock.title') }}</p>
    <p class="mt-1 text-sm text-grey-800">{{ t('stock.hint') }}</p>
    <BaseButton class="mt-3 w-full" @click="$emit('retry')">{{ t('common.retry') }}</BaseButton>
  </div>
</template>
