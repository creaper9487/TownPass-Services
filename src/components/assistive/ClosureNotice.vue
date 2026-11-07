<script setup lang="ts">
import { t, tx } from '@/i18n/assistive';
import { centerShort, formatDate } from '@/utils/assistive/centers';
import type { Center } from '@/utils/assistive/types';

defineProps<{ items: { center: Center; date: Date; reason?: string }[] }>();
</script>

<template>
  <div
    v-if="items.length"
    role="status"
    class="rounded-lg border border-secondary-200 bg-secondary-50 p-4"
  >
    <h2 class="tp-h3-semibold">{{ t('closure.title') }}</h2>
    <ul class="mt-2 flex flex-col gap-1 text-sm">
      <li v-for="(i, index) in items" :key="index">
        {{
          i.reason
            ? t('closure.lineReason', {
                center: centerShort(i.center),
                date: formatDate(i.date),
                reason: tx(i.reason)
              })
            : t('closure.line', { center: centerShort(i.center), date: formatDate(i.date) })
        }}
      </li>
    </ul>
  </div>
</template>
