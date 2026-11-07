<script setup lang="ts">
import { computed } from 'vue';
import { t, tx } from '@/i18n/assistive';
import { centerShort, formatDate } from '@/utils/assistive/centers';
import type { Center } from '@/utils/assistive/types';

const props = defineProps<{
  items: { center: Center; date: Date; reason?: string }[];
  compact?: boolean;
}>();

const lines = computed(() =>
  props.items.map((i) =>
    i.reason
      ? t('closure.lineReason', {
          center: centerShort(i.center),
          date: formatDate(i.date),
          reason: tx(i.reason)
        })
      : t('closure.line', { center: centerShort(i.center), date: formatDate(i.date) })
  )
);
</script>

<template>
  <section
    v-if="items.length && compact"
    class="flex min-w-0 items-center gap-3 rounded-lg border border-secondary-200 bg-secondary-50 px-3 py-2"
    :aria-label="t('closure.title')"
  >
    <h2 class="shrink-0 text-sm font-semibold">{{ t('closure.title') }}</h2>
    <ul class="sr-only">
      <li v-for="(line, index) in lines" :key="index">{{ line }}</li>
    </ul>
    <div class="ticker-window min-w-0 flex-1" aria-hidden="true">
      <div class="ticker-track" :style="{ '--ticker-duration': `${Math.max(lines.length * 9, 18)}s` }">
        <span class="ticker-copy">{{ lines.join('　　✦　　') }}</span>
        <span class="ticker-copy">{{ lines.join('　　✦　　') }}</span>
      </div>
    </div>
  </section>
  <div
    v-else-if="items.length"
    role="status"
    class="rounded-lg border border-secondary-200 bg-secondary-50 p-4"
  >
    <h2 class="tp-h3-semibold">{{ t('closure.title') }}</h2>
    <ul class="mt-2 flex flex-col gap-1 text-sm">
      <li v-for="(line, index) in lines" :key="index">{{ line }}</li>
    </ul>
  </div>
</template>

<style scoped>
.ticker-window {
  overflow: hidden;
}

.ticker-track {
  display: flex;
  width: max-content;
  animation: closure-ticker var(--ticker-duration) linear infinite;
}

.ticker-copy {
  flex: none;
  white-space: nowrap;
  padding-right: 3rem;
}

.ticker-window:hover .ticker-track,
.ticker-window:focus-within .ticker-track {
  animation-play-state: paused;
}

@keyframes closure-ticker {
  to {
    transform: translateX(-50%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .ticker-window {
    overflow-x: auto;
  }

  .ticker-track {
    animation: none;
  }

  .ticker-copy + .ticker-copy {
    display: none;
  }
}
</style>
