<script setup lang="ts">
import { computed, ref, watch } from 'vue';

const props = defineProps<{
  src?: string | null;
  alt?: string;
  hideOnError?: boolean;
  eager?: boolean;
}>();

const imgError = ref(false);
watch(
  () => props.src,
  () => {
    imgError.value = false;
  }
);
const failed = computed(() => !props.src || imgError.value);
</script>

<template>
  <div
    v-if="!(failed && hideOnError)"
    class="flex items-center justify-center overflow-hidden bg-white"
  >
    <img
      v-if="!failed && src"
      :src="src"
      :alt="alt ?? ''"
      :loading="eager ? 'eager' : 'lazy'"
      decoding="async"
      :fetchpriority="eager ? 'high' : 'low'"
      class="h-full w-full object-contain"
      @error="imgError = true"
    />
    <span
      v-else
      class="px-2 text-center text-sm text-grey-600"
      :aria-hidden="alt ? undefined : 'true'"
    >
      {{ alt || '無照片' }}
    </span>
  </div>
</template>
