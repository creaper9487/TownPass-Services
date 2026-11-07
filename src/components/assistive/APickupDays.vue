<script setup lang="ts">
import AIcon from './AIcon.vue';
import { t } from '@/i18n/assistive';
import { weekdayText } from '@/utils/assistive/centers';
import type { PickupDay } from '@/utils/assistive/pickup';

// 取貨期限內每一天的小卡：哪幾天中心有開、哪天是期限、哪天休館，一眼就能看到。
// 每張卡片都有文字（可前往／休館／期限），圖示只是輔助，不單靠顏色或圖示傳達。
defineProps<{ days: PickupDay[] }>();
</script>

<template>
  <ul class="flex flex-wrap gap-2" :aria-label="t('pickup.daysLabel')">
    <li
      v-for="(d, i) in days"
      :key="d.date.toISOString()"
      class="a-rise flex min-w-[6.5rem] flex-1 flex-col items-center rounded-lg border px-2 py-2.5 text-center"
      :class="
        d.open
          ? 'border-primary-600 bg-primary-50 text-grey-800'
          : 'border-dashed border-grey-300 bg-grey-50 text-grey-700'
      "
      :style="{ '--i': Math.min(i, 6) }"
    >
      <span class="text-sm">
        {{
          d.isToday ? t('pickup.todayOf', { weekday: weekdayText(d.date) }) : weekdayText(d.date)
        }}
      </span>
      <span class="text-xl font-semibold leading-7">
        {{ d.date.getMonth() + 1 }}/{{ d.date.getDate() }}
      </span>
      <span
        class="mt-1 inline-flex items-center gap-1 text-sm font-semibold"
        :class="d.open ? 'text-primary-700' : ''"
      >
        <AIcon :name="d.open ? 'check' : 'closed'" class="h-[16px] w-[16px] shrink-0" />
        {{ d.open ? t('pickup.open') : d.pastClosing ? t('pickup.passed') : t('pickup.closed') }}
      </span>
      <span
        v-if="d.isDeadline"
        class="mt-1.5 rounded-full border border-orange-700 bg-white px-2 text-sm font-semibold text-orange-700"
      >
        {{ t('pickup.deadline') }}
      </span>
    </li>
  </ul>
</template>
