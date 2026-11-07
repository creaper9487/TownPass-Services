<script setup lang="ts">
import { computed } from 'vue';
import AIcon from './AIcon.vue';
import { t } from '@/i18n/assistive';
import { formatDate } from '@/utils/assistive/centers';
import type { PickupRemaining } from '@/utils/assistive/pickup';

// 還剩幾個開館日可以去取貨。只剩一天或沒有時改用橘色／紅色外框與警示圖示，並且一定有一句話說明。
const props = defineProps<{ remaining: PickupRemaining }>();

const text = computed(() => {
  const r = props.remaining;
  if (r.count === 0) return t('pickup.none');
  if (r.count === 1) {
    return r.lastIsToday
      ? t('pickup.lastToday')
      : t('pickup.lastOn', { date: formatDate(r.last!) });
  }
  return t('pickup.remaining', { n: r.count });
});
const level = computed(() =>
  props.remaining.count === 0 ? 'none' : props.remaining.count === 1 ? 'last' : 'ok'
);
</script>

<template>
  <p
    role="status"
    class="inline-flex items-start gap-2 rounded-lg border px-3 py-2 text-sm font-semibold"
    :class="{
      'border-primary-600 bg-primary-50 text-primary-700': level === 'ok',
      'border-orange-700 bg-orange-50 text-orange-700': level === 'last',
      'border-red-700 bg-red-50 text-red-700': level === 'none'
    }"
  >
    <AIcon :name="level === 'ok' ? 'clock' : 'alert'" class="mt-px h-[20px] w-[20px] shrink-0" />
    <span>{{ text }}</span>
  </p>
</template>
