<script setup lang="ts">
defineProps<{ id?: string }>();
</script>

<template>
  <p
    :id="id"
    class="a-drop mt-2 flex items-start justify-end gap-1.5 text-right text-sm font-semibold text-red-600"
  >
    <svg class="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5" />
      <path
        d="M8 4.5v4.2M8 11v.01"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
      />
    </svg>
    <span><slot /></span>
  </p>
</template>
