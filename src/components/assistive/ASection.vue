<script setup lang="ts">
defineProps<{ title?: string; hint?: string; grey?: boolean }>();
</script>

<template>
  <section class="px-4 py-5" :class="{ 'bg-grey-50': grey }">
    <h2 v-if="title" class="tp-h3-semibold text-primary-700">{{ title }}</h2>
    <p v-if="hint" class="mt-1 text-sm text-grey-700">{{ hint }}</p>
    <div :class="{ 'mt-4': title || hint }">
      <slot />
    </div>
  </section>
  <div class="h-2 bg-grey-50 last:hidden" aria-hidden="true" />
</template>
