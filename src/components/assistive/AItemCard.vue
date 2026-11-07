<script setup lang="ts">
import AImage from './AImage.vue';
import { tx, zhAttr } from '@/i18n/assistive';
import type { VariantInfo } from '@/utils/assistive/catalog';

// 一件輔具：照片＋品名＋分類＋規格，各自一行。不要把這幾項用「・」串成一長串，使用者看不出哪一段是什麼。
// 照片只是輔助，文字仍然完整；照片載入失敗就不顯示。
defineProps<{ item: VariantInfo; compact?: boolean }>();
</script>

<template>
  <div class="a-item-card">
    <div class="flex items-start gap-3">
      <AImage
        v-if="item.image"
        :src="item.image"
        hide-on-error
        class="a-item-photo shrink-0 rounded bg-grey-50"
        :class="compact ? 'h-[48px] w-[48px]' : 'h-[64px] w-[64px]'"
      />
      <div class="min-w-0 flex-1 text-left">
        <p class="text-sm text-grey-700">{{ tx(item.category) }}</p>
        <p :lang="zhAttr" class="break-words text-base font-semibold">{{ item.name }}</p>
        <p
          v-if="item.specs.length"
          :lang="zhAttr"
          class="mt-0.5 whitespace-pre-line break-words text-sm text-grey-700"
        >
          {{ item.specs.join('\n') }}
        </p>
      </div>
    </div>
  </div>
</template>
