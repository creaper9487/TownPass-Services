<script setup lang="ts">
import { computed } from 'vue';
import AIcon from './AIcon.vue';
import { t, zhAttr } from '@/i18n/assistive';
import { useTaipeiNow } from '@/utils/assistive/time';
import { centerName, hoursText, isOpenAt, openDaysText } from '@/utils/assistive/centers';
import type { Center } from '@/utils/assistive/types';

const props = defineProps<{ center: Center; badge?: string }>();
const now = useTaipeiNow();
const open = computed(() => isOpenAt(props.center, now.value));
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center gap-2">
      <h3 class="tp-h3-semibold">{{ centerName(center) }}</h3>
      <span v-if="badge" class="tp-tag">
        {{ badge }}
      </span>
    </div>
    <p :lang="zhAttr" class="mt-1 text-base">
      {{ center.address }}
      <span v-if="center.addressNote" class="block text-sm text-grey-700">
        {{ center.addressNote }}
      </span>
    </p>
    <p class="mt-1 text-base text-grey-700">
      {{ openDaysText(center) }} {{ hoursText(center) }}
      <span
        class="ml-1 inline-flex items-center gap-1 whitespace-nowrap font-semibold"
        :class="open ? 'text-primary-700' : 'text-grey-700'"
      >
        <AIcon :name="open ? 'check' : 'closed'" class="h-[1.1em] w-[1.1em] shrink-0" />
        {{ open ? t('center.open') : t('center.closedNow') }}
      </span>
    </p>
  </div>
</template>
