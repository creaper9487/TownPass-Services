<script setup lang="ts">
import { computed } from 'vue';
import { useTaipeiNow } from '@/utils/assistive/time';
import { hoursText, isOpenAt, openDaysText } from '@/utils/assistive/centers';
import type { Center } from '@/utils/assistive/types';

const props = defineProps<{ center: Center; badge?: string }>();
const now = useTaipeiNow();
const open = computed(() => isOpenAt(props.center, now.value));
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center gap-2">
      <h3 class="tp-h3-semibold">{{ center.name }}</h3>
      <span v-if="badge" class="tp-tag">
        {{ badge }}
      </span>
    </div>
    <p class="mt-1 text-base">
      {{ center.address }}
      <span v-if="center.addressNote" class="block text-sm text-grey-700">
        {{ center.addressNote }}
      </span>
    </p>
    <p class="mt-1 text-base text-grey-700">
      {{ openDaysText(center) }} {{ hoursText(center) }}
      <span
        class="ml-1 whitespace-nowrap font-semibold"
        :class="open ? 'text-primary-700' : 'text-grey-700'"
      >
        {{ open ? '● 開館中' : '○ 目前休館' }}
      </span>
    </p>
  </div>
</template>
