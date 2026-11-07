<script setup lang="ts">
import { computed } from 'vue';
import { t } from '@/i18n/assistive';
import { useAssistiveNative } from '@/composables/useAssistiveNative';

// 直接內嵌 YouTube（隱私加強模式的網址）。播放器自己的控制列有鍵盤與讀屏支援；
// 萬一在這支手機上播不出來，下方留一個在 YouTube 開啟的備用入口。
const props = defineProps<{ id: string; title: string }>();
const native = useAssistiveNative();
const src = computed(
  () => `https://www.youtube-nocookie.com/embed/${props.id}?rel=0&hl=zh-TW&playsinline=1`
);
</script>

<template>
  <figure>
    <div class="aspect-video w-full overflow-hidden rounded-lg bg-grey-100">
      <iframe
        :src="src"
        :title="title"
        class="h-full w-full border-0"
        loading="lazy"
        allow="fullscreen; picture-in-picture; encrypted-media"
        allowfullscreen
        referrerpolicy="strict-origin-when-cross-origin"
      />
    </div>
    <figcaption class="mt-2 text-sm text-grey-700">
      {{ t('education.videoFail') }}
      <button
        type="button"
        class="a11y-focus inline-flex min-h-6 items-center font-semibold text-primary-700 underline"
        @click="native.openLink(`https://www.youtube.com/watch?v=${id}`)"
      >
        {{ t('education.openYoutube') }}
      </button>
    </figcaption>
  </figure>
</template>
