<script setup>
defineProps({
  label: { type: String, required: true },
  active: { type: Boolean, default: false }
});
defineEmits(['click']);
</script>

<template>
  <button 
    class="px-3 py-2 rounded-xl border transition-all duration-200 text-sm font-medium whitespace-nowrap"
    :class="active 
      ? 'bg-primary-500 border-primary-600 text-white shadow-md' 
      : 'bg-white border-grey-200 text-grey-700 hover:border-primary-300 hover:bg-primary-50'"
    @click="$emit('click')"
  >
    <slot name="icon" />
    <span>{{ label }}</span>
  </button>
</template>

<style scoped></style>
