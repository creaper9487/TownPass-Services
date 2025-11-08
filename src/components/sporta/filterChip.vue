<script setup>
defineProps({
  label: { type: String, required: true },
  active: { type: Boolean, default: false }
});
defineEmits(['click']);
</script>

<template>
  <button class="chip" :class="{ active }" @click="$emit('click')">
    <slot name="icon" />
    <span class="t">{{ label }}</span>
  </button>
</template>

<style scoped>
.chip {
  -webkit-tap-highlight-color: transparent;
  appearance: none; border: 0; cursor: pointer;
  padding: 8px 12px; margin: 0 6px 0 0;
  border-radius: 14px;
  background: rgba(255,255,255,.16);
  border: 1px solid rgba(255,255,255,.28);
  color: var(--text);
  font-size: 13px;
  display: inline-flex; align-items: center; gap: 6px;
  backdrop-filter: blur(var(--blur)); -webkit-backdrop-filter: blur(var(--blur));
  box-shadow: inset 0 1px 0 rgba(255,255,255,.25);
  transition: background .2s ease, transform .15s ease;
}
.chip:active { transform: scale(.97); }
.chip.active { background: rgba(255,255,255,.7); color: #111315; }
.t { white-space: nowrap; }
</style>
