<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { direction } from '@/composables/useAssistiveMotion';
import { useRoute } from 'vue-router';
import { serviceShortTitle, services } from '@/utils/assistive/services';
import type { ServiceId } from '@/utils/assistive/types';
import { t } from '@/i18n/assistive';

const props = defineProps<{
  title: string;
  lead?: string;
  /** lead 是另一種語言（英文介面下的官方中文原文）時的 lang 屬性 */
  leadLang?: string;
  /** 目前步驟與總步數；首頁等非流程頁不傳 */
  step?: number;
  total?: number;
  /** 首頁：App 標題列已經寫了服務名稱，頁內不再畫一條標題，只留給讀屏與焦點用 */
  hideHeader?: boolean;
}>();

const heading = ref<HTMLElement>();
// 流程頁的步驟列前面帶上服務名稱（例如「輔具評估・步驟 1／5」），不用從標題猜現在在辦什麼。
const route = useRoute();
const serviceName = computed(() => {
  const id = route.params.service as ServiceId;
  return services[id] ? serviceShortTitle(id) : '';
});
const stepLine = computed(() => {
  const params = { n: props.step ?? 0, m: props.total ?? 0 };
  return serviceName.value
    ? t('step.withService', { service: serviceName.value, ...params })
    : t('step.line', params);
});
// 進度條從上一步的位置長到這一步
const ratio = computed(() => (props.step && props.total ? props.step / props.total : 0));
const shownRatio = ref(props.step && props.total ? Math.max(props.step - 1, 0) / props.total : 0);
const enterClass = direction.value === 'back' ? 'a-enter-back' : 'a-enter-forward';
const footerEl = ref<HTMLElement>();
const isAndroid = /Android/i.test(navigator.userAgent);

// 底部操作列平常固定在畫面底部；鍵盤跳出或字級放大到佔掉太多畫面時改成跟著內容走，避免蓋住正在輸入的欄位。
const footerStatic = ref(false);
let tallest = 0;
let observer: ResizeObserver | undefined;
const viewportHeight = () => window.visualViewport?.height ?? window.innerHeight;
const measure = () => {
  const height = viewportHeight();
  tallest = Math.max(tallest, height);
  const keyboardOpen = height < tallest * 0.8;
  const tooTall = (footerEl.value?.getBoundingClientRect().height ?? 0) > height * 0.3;
  footerStatic.value = keyboardOpen || tooTall;
};

// 換頁後把焦點移到標題：讀屏使用者能立刻聽到「現在在哪一步」，鍵盤使用者也不會停在上一頁的位置。
onMounted(async () => {
  window.scrollTo({ top: 0 });
  await nextTick();
  setTimeout(() => (shownRatio.value = ratio.value), 30);
  heading.value?.focus({ preventScroll: true });
  measure();
  window.addEventListener('resize', measure);
  window.visualViewport?.addEventListener('resize', measure);
  if (footerEl.value && 'ResizeObserver' in window) {
    observer = new ResizeObserver(measure);
    observer.observe(footerEl.value);
  }
});
onBeforeUnmount(() => {
  window.removeEventListener('resize', measure);
  window.visualViewport?.removeEventListener('resize', measure);
  observer?.disconnect();
});
</script>

<template>
  <div
    class="assistive-scope flex min-h-screen flex-col bg-white text-grey-800"
    :class="{ 'assistive-android': isAndroid }"
  >
    <main class="flex-1" :class="enterClass">
      <header :class="props.hideHeader ? 'sr-only' : 'bg-grey-50 px-4 pb-4 pt-5'">
        <template v-if="props.step && props.total">
          <p class="text-sm text-grey-700" aria-hidden="true">
            {{ stepLine }}
          </p>
          <div class="mt-2 h-1 rounded-full bg-grey-100" aria-hidden="true">
            <div
              class="a-progress h-1 rounded-full bg-primary-500"
              :style="{ width: `${shownRatio * 100}%` }"
            />
          </div>
        </template>
        <h1 ref="heading" tabindex="-1" class="tp-h2 outline-none" :class="{ 'mt-3': props.step }">
          <span v-if="props.step && props.total && serviceName !== props.title" class="sr-only">
            {{ t('step.sr', { service: serviceName, n: props.step, m: props.total }) }}
          </span>
          {{ props.title }}
        </h1>
        <p v-if="props.lead" :lang="props.leadLang" class="mt-2 text-sm text-grey-700">
          {{ props.lead }}
        </p>
      </header>
      <slot />
    </main>

    <footer
      v-if="$slots.footer"
      ref="footerEl"
      class="border-t border-grey-100 bg-white px-4 pt-3 pb-[max(1rem,env(safe-area-inset-bottom))]"
      :class="footerStatic ? 'static' : 'sticky bottom-0 z-10'"
    >
      <slot name="footer" />
    </footer>
  </div>
</template>
