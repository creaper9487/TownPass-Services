<script setup lang="ts">
import { RouterLink, type RouteLocationRaw } from 'vue-router';
import AImage from './AImage.vue';

// 台北通「服務」頁的卡片：白底細框圓角 6，標題在左、圖示在右；主要功能用青色漸層大卡，下方放官方照片。
defineProps<{
  title: string;
  description?: string;
  to: RouteLocationRaw;
  /** 一般卡片右側的圖示 */
  icon?: string;
  /** 主要功能：青色漸層、白字，下方一排照片 */
  hero?: boolean;
  photos?: string[];
}>();
const emit = defineEmits<{ (e: 'click'): void }>();
</script>

<template>
  <RouterLink
    :to="to"
    class="a11y-focus block overflow-hidden rounded-[6px]"
    :class="
      hero
        ? 'assistive-hero bg-gradient-to-tl from-primary-700 to-primary-800 p-4 text-white'
        : 'flex min-h-20 items-center gap-3 border border-grey-100 bg-white px-4 py-3'
    "
    @click="emit('click')"
  >
    <template v-if="hero">
      <span class="tp-h3-semibold block">{{ title }}</span>
      <span v-if="photos?.length" class="assistive-hero-photos mt-3 flex gap-2" aria-hidden="true">
        <AImage
          v-for="p in photos"
          :key="p"
          :src="p"
          eager
          hide-on-error
          class="h-[80px] min-w-0 flex-1 rounded-[3px] p-1"
        />
      </span>
    </template>
    <template v-else>
      <span class="min-w-0 flex-1">
        <span class="tp-h3-semibold block text-primary-700">{{ title }}</span>
        <span v-if="description" class="mt-1 block text-sm leading-relaxed text-grey-700">
          {{ description }}
        </span>
      </span>
      <img v-if="icon" :src="icon" alt="" class="h-[48px] w-[48px] shrink-0" />
    </template>
  </RouterLink>
</template>
