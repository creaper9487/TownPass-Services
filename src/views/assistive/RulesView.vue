<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import ASection from '@/components/assistive/ASection.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { t, zhAttr } from '@/i18n/assistive';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { useRouter } from 'vue-router';
import { officialCenterRows } from '@/utils/assistive/centers';
import { BORROW_RULES } from '@/utils/assistive/services';

const emit = defineEmits<{ agree: [] }>();
defineProps<{ readOnly?: boolean }>();
const native = useAssistiveNative();
const router = useRouter();
const rulesScroll = ref<HTMLElement>();
const currentInput = ref<HTMLInputElement>();
const readToEnd = ref(false);
const checked = ref(BORROW_RULES.consents.map(() => false));
const currentIndex = computed(() => checked.value.findIndex((value) => !value));
const allChecked = computed(() => currentIndex.value === -1);

const checkScrollBottom = () => {
  const area = rulesScroll.value;
  if (area && area.scrollTop + area.clientHeight >= area.scrollHeight - 16) {
    readToEnd.value = true;
  }
};

const checkCurrent = (event: Event) => {
  const index = currentIndex.value;
  if (index < 0) return;
  checked.value[index] = (event.target as HTMLInputElement).checked;
};

const focusCurrent = () => currentInput.value?.focus({ preventScroll: true });
const reviewAgain = async () => {
  checked.value = BORROW_RULES.consents.map(() => false);
  await nextTick();
  focusCurrent();
};

const agree = () => {
  if (readToEnd.value && allChecked.value) emit('agree');
};

onMounted(() => {
  window.requestAnimationFrame(checkScrollBottom);
  window.addEventListener('resize', checkScrollBottom);
});
onBeforeUnmount(() => window.removeEventListener('resize', checkScrollBottom));
</script>

<template>
  <div
    class="assistive-scope flex h-dvh flex-col items-center justify-start bg-grey-50 p-3 text-grey-800"
  >
    <div
      class="rules-card flex w-full max-w-xl flex-col overflow-hidden rounded-xl border border-grey-200 bg-white shadow-sm"
    >
      <header class="shrink-0 border-b border-grey-100 bg-grey-50 px-4 py-3">
        <h1 id="borrow-rules-title" class="tp-h2">{{ t('borrow.rules.title') }}</h1>
      </header>

      <div
        ref="rulesScroll"
        class="min-h-0 flex-1 overflow-y-auto overscroll-contain"
        role="region"
        aria-labelledby="borrow-rules-title"
        tabindex="0"
        @scroll="checkScrollBottom"
      >
        <ASection>
          <div :lang="zhAttr" class="flex flex-col gap-3 text-base">
            <template v-for="[k, v] in BORROW_RULES.items" :key="k">
              <h3 v-if="!v" class="tp-h3-semibold mt-2">{{ k }}</h3>
              <p v-else>
                <span class="font-semibold">{{ k }}</span
                ><span>{{ v }}</span>
              </p>
            </template>
          </div>
          <p :lang="zhAttr" class="mt-4 text-sm text-grey-700">{{ BORROW_RULES.footnote }}</p>
        </ASection>

        <ASection :title="t('borrow.rules.centersHeading')">
          <ul class="flex flex-col gap-3">
            <li
              v-for="c in officialCenterRows"
              :key="c.name"
              :lang="zhAttr"
              class="rounded-lg border border-grey-200 p-3 text-base"
            >
              <p class="font-semibold">{{ c.name }}</p>
              <p class="mt-1">{{ c.hours }}</p>
              <p>{{ c.address }}</p>
              <button
                type="button"
                class="a11y-focus -my-1 flex min-h-11 items-center whitespace-nowrap font-semibold text-primary-700 underline"
                @click="native.callPhone(c.phone)"
              >
                {{ c.phone }}
              </button>
            </li>
          </ul>
          <p :lang="zhAttr" class="mt-4 text-sm text-grey-700">{{ BORROW_RULES.consentNote }}</p>
        </ASection>
      </div>

      <footer
        class="shrink-0 border-t border-grey-100 bg-white px-4 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]"
      >
        <BaseButton
          v-if="readOnly"
          outline
          class="w-full"
          @click="router.replace({ name: 'assistive-home' })"
        >
          {{ t('education.back') }}
        </BaseButton>
        <template v-else>
          <div v-if="!readToEnd" role="status" class="text-center text-sm text-grey-700">
            {{ t('borrow.rules.scrollHint') }}
          </div>
          <template v-else>
            <Transition name="consent-fade" mode="out-in" @after-enter="focusCurrent">
              <div v-if="!allChecked" :key="currentIndex" class="min-w-0">
                <p class="mb-2 text-sm font-semibold text-primary-700" aria-live="polite">
                  {{
                    t('borrow.rules.progress', {
                      n: currentIndex + 1,
                      m: BORROW_RULES.consents.length
                    })
                  }}
                </p>
                <label
                  class="flex cursor-pointer items-start gap-3 rounded-lg border border-grey-200 p-3 focus-within:border-primary-600"
                >
                  <input
                    ref="currentInput"
                    type="checkbox"
                    class="mt-1 h-5 w-5 shrink-0 accent-primary-600"
                    :checked="checked[currentIndex]"
                    @change="checkCurrent"
                  />
                  <span :lang="zhAttr" class="min-w-0 text-sm leading-relaxed">
                    {{ BORROW_RULES.consents[currentIndex] }}
                  </span>
                </label>
              </div>
              <div v-else key="complete" class="flex items-center justify-between gap-3 text-sm">
                <span role="status" class="font-semibold text-primary-700">{{
                  t('borrow.rules.complete')
                }}</span>
                <button type="button" class="shrink-0 underline" @click="reviewAgain">
                  {{ t('borrow.rules.reviewAgain') }}
                </button>
              </div>
            </Transition>
          </template>

          <div class="mt-3 grid grid-cols-2 gap-2">
            <BaseButton outline @click="router.replace({ name: 'home' })">
              {{ t('borrow.rules.disagree') }}
            </BaseButton>
            <BaseButton :disabled="!readToEnd || !allChecked" @click="agree">
              {{ t('borrow.rules.agree') }}
            </BaseButton>
          </div>
        </template>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.rules-card {
  height: min(82dvh, 760px);
  max-height: calc(100dvh - 1.5rem);
}

.consent-fade-enter-active,
.consent-fade-leave-active {
  transition:
    opacity 220ms ease,
    transform 220ms ease;
}

.consent-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.consent-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (prefers-reduced-motion: reduce) {
  .consent-fade-enter-active,
  .consent-fade-leave-active {
    transition: none;
  }
}
</style>
