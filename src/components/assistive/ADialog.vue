<script setup lang="ts">
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue';
import { t } from '@/i18n/assistive';

// 輔具預約用的對話框：外觀沿用台北通共用對話框（白底、上方圖示、標題、下方兩個文字按鈕），
// 但共用的 BaseDialog 被搬到頁面外層，吃不到輔具預約的無障礙設定，所以另外做：
// 按鈕至少 48px 高、主色用 Primary/700（Primary/500 配白底只有 2.4:1）、有鍵盤焦點外框、字重只用 600。
const props = defineProps<{
  title?: string;
  content?: string;
  negativeText?: string;
  positiveText?: string;
  isCheck?: boolean;
}>();

const emit = defineEmits(['onPositiveClick', 'onNegativeClick']);
const isOpen = defineModel({ default: false });
const isAndroid = /Android/i.test(navigator.userAgent);

const onPositiveClick = () => {
  isOpen.value = false;
  emit('onPositiveClick');
};
const onNegativeClick = () => {
  isOpen.value = false;
  emit('onNegativeClick');
};
</script>

<template>
  <!-- 按 Esc 或點背景＝選比較保守的那個（「保留」）；只有一個按鈕時就是關閉。
       TransitionRoot／TransitionChild 裡只能有一個元素，註解也不能放進去。 -->
  <TransitionRoot appear :show="isOpen" as="template">
    <Dialog
      as="div"
      :open="isOpen"
      class="assistive-scope relative z-[9999]"
      :class="{ 'assistive-android': isAndroid }"
      @close="negativeText ? onNegativeClick() : onPositiveClick()"
    >
      <div class="fixed inset-0 overflow-y-auto bg-black/40">
        <div class="flex min-h-full items-center justify-center p-4">
          <TransitionChild
            as="template"
            enter="duration-200 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-150 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel
              class="flex w-full max-w-sm flex-col overflow-hidden rounded-lg bg-white text-grey-800"
            >
              <div class="px-5 pb-5 pt-6">
                <img
                  v-if="props.isCheck"
                  src="@/assets/images/check-icon.svg"
                  alt=""
                  class="mx-auto mb-3 w-20"
                />
                <DialogTitle v-if="props.title" class="text-center text-xl font-semibold">
                  {{ title }}
                </DialogTitle>
                <div class="mt-3">
                  <slot name="content">
                    <p v-if="content" class="whitespace-pre-line text-center text-base">
                      {{ content }}
                    </p>
                  </slot>
                </div>
              </div>
              <div
                class="grid border-t border-grey-200"
                :class="negativeText ? 'grid-cols-2 divide-x divide-grey-200' : 'grid-cols-1'"
              >
                <button
                  v-if="negativeText"
                  type="button"
                  class="min-h-12 px-3 py-2 text-base font-semibold text-grey-700 focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary-600"
                  @click="onNegativeClick"
                >
                  {{ negativeText }}
                </button>
                <button
                  type="button"
                  class="min-h-12 px-3 py-2 text-base font-semibold text-primary-700 focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary-600"
                  @click="onPositiveClick"
                >
                  {{ positiveText || t('common.confirm') }}
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
