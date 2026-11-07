<script setup lang="ts">
import { LANGS, lang, setLang, t } from '@/i18n/assistive';
</script>

<template>
  <div role="group" :aria-label="t('lang.switchLabel')" class="flex gap-2">
    <button
      v-for="l in LANGS"
      :key="l.value"
      type="button"
      :lang="l.value"
      :aria-pressed="lang === l.value"
      class="a11y-focus min-h-11 flex-1 rounded-lg border px-4 text-base font-semibold"
      :class="
        lang === l.value
          ? 'border-primary-700 bg-primary-700 text-white'
          : 'border-primary-700 bg-white text-primary-700'
      "
      @click="setLang(l.value)"
    >
      {{ l.label }}
    </button>
  </div>
</template>
