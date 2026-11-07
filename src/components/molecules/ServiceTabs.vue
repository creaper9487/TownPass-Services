<script setup lang="ts">
import { ref } from 'vue';
import type { TabsProps } from '@/interfaces/tab-props.interface';

const props = withDefaults(defineProps<TabsProps>(), {
  tabList: () => [
    {
      id: 1,
      title: '申辦'
    },
    {
      id: 2,
      title: '查詢'
    }
  ],
  contentType: false
});

const activeTab = defineModel({ default: 0 });
const buttons = ref<HTMLButtonElement[]>([]);

// 方向鍵切換分頁（只有作用中的分頁在 Tab 順序裡）
const onKeydown = (event: KeyboardEvent) => {
  const last = props.tabList.length - 1;
  const next: Record<string, number> = {
    ArrowRight: activeTab.value >= last ? 0 : activeTab.value + 1,
    ArrowLeft: activeTab.value <= 0 ? last : activeTab.value - 1,
    Home: 0,
    End: last
  };
  if (!(event.key in next)) return;
  event.preventDefault();
  // defineModel 要等下一個 tick 才會更新，焦點直接給目標分頁
  const target = next[event.key];
  activeTab.value = target;
  buttons.value[target]?.focus();
};
</script>

<template>
  <div
    class="tabs"
    role="tablist"
    :aria-label="listLabel"
    :class="{ '!grid-cols-3': tabList.length % 3 === 0, 'tabs__content-type': props.contentType }"
    @keydown="onKeydown"
  >
    <button
      v-for="(item, index) in props.tabList"
      :id="idPrefix ? `${idPrefix}-tab-${index}` : undefined"
      :key="item.id"
      :ref="(el) => (buttons[index] = el as HTMLButtonElement)"
      type="button"
      role="tab"
      :aria-selected="index === activeTab"
      :aria-controls="idPrefix ? `${idPrefix}-panel` : undefined"
      :aria-label="item.label"
      :tabindex="index === activeTab ? 0 : -1"
      class="tab-label a11y-focus"
      :class="{
        'tab-label--active': index === activeTab && !props.contentType,
        'tab-label__content-type': props.contentType,
        'tab-label__content-type--active': index === activeTab && props.contentType
      }"
      @click="activeTab = index"
    >
      <span class="inline-flex items-center justify-center gap-1.5">
        <slot name="icon" :item="item" :active="index === activeTab" />
        {{ item.title }}
      </span>
    </button>
    <div
      class="slider"
      aria-hidden="true"
      :class="{ 'slider__content-type': props.contentType }"
      :style="{ transform: `translate(calc(100%*${activeTab}))` }"
    />
  </div>
</template>

<style lang="postcss">
.tabs {
  @apply grid grid-cols-2;
  @apply px-4 pt-2;
  @apply border-b border-b-grey-300;

  &__content-type {
    @apply px-0;
  }
}

.tab-label {
  @apply text-grey-700 bg-white font-bold mb-2;

  &__content-type {
    @apply rounded-t-[10px] border-x border-t border-grey-200;
    @apply px-3 py-2 mb-0;
    @apply transition-colors;

    &--active {
      @apply bg-primary-50 border-transparent;
    }
  }

  &--active {
    @apply text-primary-500;
  }
}

.slider {
  @apply relative bottom-0;
  @apply transition-all duration-500 motion-reduce:transition-none;
  @apply bg-primary-500;
  @apply w-full h-0.5;

  &__content-type {
    @apply bg-[#5AB4C5];
  }
}
</style>
