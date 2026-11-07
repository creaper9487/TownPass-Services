<script setup lang="ts">
import { computed } from 'vue';
import { t } from '@/i18n/assistive';
import type { EffectiveStatus } from '@/utils/assistive/api';
import type { ServiceId } from '@/utils/assistive/types';

// 預約進度：已預約（或已送出）→ 中心已確認 → 已完成。取消與逾期是另一條路，用兩格表示「到這裡就結束了」。
// 是 <ol>，每一格都有文字與狀態（已達成／目前／尚未），讀屏不會漏掉任何資訊；圖形只是輔助。
const props = defineProps<{ status: EffectiveStatus; service: ServiceId }>();

type NodeState = 'done' | 'now' | 'todo' | 'ended';
interface Node {
  key: string;
  state: NodeState;
}

const nodes = computed<Node[]>(() => {
  const first = props.service === 'borrow' ? 'booked' : 'submitted';
  if (props.status === 'cancelled' || props.status === 'expired') {
    return [
      { key: first, state: 'done' },
      { key: props.status, state: 'ended' }
    ];
  }
  const at = props.status === 'completed' ? 2 : props.status === 'confirmed' ? 1 : 0;
  return [first, 'confirmed', 'completed'].map((key, i) => ({
    key,
    state: props.status === 'completed' || i < at ? 'done' : i === at ? 'now' : 'todo'
  }));
});

const srState = (s: NodeState) =>
  s === 'done'
    ? t('progress.srDone')
    : s === 'now'
      ? t('progress.srNow')
      : s === 'ended'
        ? ''
        : t('progress.srTodo');
</script>

<template>
  <ol
    class="grid gap-0"
    :class="nodes.length === 2 ? 'grid-cols-2' : 'grid-cols-3'"
    :aria-label="t('progress.label')"
  >
    <li
      v-for="(n, i) in nodes"
      :key="n.key"
      class="relative flex flex-col items-center px-1 text-center"
    >
      <!-- 連到前一格的線；前一格已達成才用主色 -->
      <span
        v-if="i > 0"
        class="absolute left-[-50%] top-[14px] h-0.5 w-full"
        :class="n.state === 'done' || n.state === 'now' ? 'bg-primary-600' : 'bg-grey-200'"
        aria-hidden="true"
      />
      <span
        class="relative flex h-[28px] w-[28px] items-center justify-center rounded-full border-2"
        :class="{
          'border-primary-700 bg-primary-700 text-white': n.state === 'done',
          'border-primary-700 bg-white': n.state === 'now',
          'border-grey-300 bg-white': n.state === 'todo',
          'border-grey-500 bg-grey-500 text-white': n.state === 'ended'
        }"
        aria-hidden="true"
      >
        <svg
          v-if="n.state === 'done'"
          class="h-[16px] w-[16px]"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M3.5 8.5l3 3 6-6.5" />
        </svg>
        <span v-else-if="n.state === 'now'" class="h-[10px] w-[10px] rounded-full bg-primary-700" />
        <svg
          v-else-if="n.state === 'ended'"
          class="h-[14px] w-[14px]"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
        >
          <path d="M4.5 4.5l7 7M11.5 4.5l-7 7" />
        </svg>
      </span>
      <span
        class="mt-1.5 text-sm"
        :class="n.state === 'todo' ? 'text-grey-700' : 'font-semibold text-grey-800'"
      >
        {{ t(`progress.${n.key}`) }}<span class="sr-only"> {{ srState(n.state) }}</span>
      </span>
    </li>
  </ol>
</template>
