<script setup lang="ts">
import { formatDate } from '@/utils/assistive/centers';
import type { Center } from '@/utils/assistive/types';

defineProps<{ items: { center: Center; date: Date; reason?: string }[] }>();
</script>

<template>
  <div
    v-if="items.length"
    role="status"
    class="rounded-lg border border-secondary-200 bg-secondary-50 p-4"
  >
    <h2 class="tp-h3-semibold">近期休館公告</h2>
    <ul class="mt-2 flex flex-col gap-1 text-sm">
      <li v-for="(i, index) in items" :key="index">
        {{ i.center.shortName }}輔具中心 {{ formatDate(i.date) }} 休館<span v-if="i.reason">
          ：{{ i.reason }}
        </span>
      </li>
    </ul>
  </div>
</template>
