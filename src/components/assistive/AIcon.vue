<script setup lang="ts">
// 輔具預約流程內用的線條圖示：24 格、線寬 1.75、圓端點，顏色跟著文字（currentColor）。
// 圖示只裝飾，旁邊一定有文字；因此一律 aria-hidden，不單靠圖示傳達意思。
export type IconName =
  | 'assess'
  | 'repair'
  | 'info'
  | 'wheelchair'
  | 'home'
  | 'brace'
  | 'eye'
  | 'chat'
  | 'monitor'
  | 'stairs'
  | 'more';

defineProps<{ name: IconName }>();
</script>

<template>
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <template v-if="name === 'assess'">
      <rect x="5" y="4.5" width="14" height="16.5" rx="2" />
      <rect x="9" y="2.5" width="6" height="4" rx="1" />
      <path d="M9 13.5l2.2 2.2L15.5 11" />
    </template>
    <template v-else-if="name === 'repair'">
      <path
        d="M14.8 3.8a4.5 4.5 0 0 0-4.2 6.1l-6.2 6.2a2 2 0 0 0 2.8 2.8l6.2-6.2a4.5 4.5 0 0 0 6.1-4.2l-2.9 2.1-2.4-.5-.5-2.4z"
      />
    </template>
    <template v-else-if="name === 'info'">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5.5M12 7.6v.01" />
    </template>
    <template v-else-if="name === 'wheelchair'">
      <circle cx="10.5" cy="4.3" r="1.6" />
      <path d="M10.5 7.6v5.4h5.6l2.4 5" />
      <path d="M7.6 10.8a5.6 5.6 0 1 0 8 7.4" />
    </template>
    <template v-else-if="name === 'home'">
      <path d="M4 11l8-6.5 8 6.5v8.5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1z" />
      <path d="M10 20.5v-5h4v5" />
    </template>
    <template v-else-if="name === 'brace'">
      <rect x="2.5" y="8.5" width="19" height="7" rx="3.5" transform="rotate(-45 12 12)" />
      <rect x="9.5" y="9.5" width="5" height="5" rx="1" transform="rotate(-45 12 12)" />
    </template>
    <template v-else-if="name === 'eye'">
      <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z" />
      <circle cx="12" cy="12" r="3" />
    </template>
    <template v-else-if="name === 'chat'">
      <path
        d="M5 5h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-7l-4 3.5V17H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z"
      />
    </template>
    <template v-else-if="name === 'monitor'">
      <rect x="3" y="4" width="18" height="12" rx="2" />
      <path d="M8 20h8M12 16v4" />
    </template>
    <template v-else-if="name === 'stairs'">
      <path d="M3 20h4.5v-4.5H12V11h4.5V6.5H21" />
    </template>
    <template v-else>
      <circle cx="6" cy="12" r="1.25" fill="currentColor" />
      <circle cx="12" cy="12" r="1.25" fill="currentColor" />
      <circle cx="18" cy="12" r="1.25" fill="currentColor" />
    </template>
  </svg>
</template>
