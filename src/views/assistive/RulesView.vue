<script setup lang="ts">
import { computed, nextTick, ref } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AChoice from '@/components/assistive/AChoice.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { t, zhAttr } from '@/i18n/assistive';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { officialCenterRows } from '@/utils/assistive/centers';
import { BORROW_RULES } from '@/utils/assistive/services';

const native = useAssistiveNative();

// 官方「二手輔具借用須知」：原文照登，三項同意都勾選後按「我同意」。
const store = useAssistiveStore();
const flow = useAssistiveFlow();

const checked = ref(BORROW_RULES.consents.filter((_, i) => store.consents[i]));
const hasError = ref(false);
const error = computed(() => (hasError.value ? t('borrow.rules.consentError') : ''));

const CONSENT_ID = 'borrow-consents';

// 還沒勾完就按「我同意」：把畫面帶到三項注意事項，錯誤訊息和還沒勾的那幾項才看得到；
// 焦點也移到第一個沒勾的選項，讀屏與鍵盤使用者會直接落在要處理的地方。
const guideToConsents = async () => {
  await nextTick();
  const group = document.getElementById(CONSENT_ID);
  if (!group) return;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  group.scrollIntoView({ block: 'start', behavior: reduce ? 'auto' : 'smooth' });
  group.querySelector<HTMLInputElement>('input:not(:checked)')?.focus({ preventScroll: true });
};

const agree = () => {
  store.consents = BORROW_RULES.consents.map((a) => checked.value.includes(a));
  if (!store.consents.every(Boolean)) {
    hasError.value = true;
    guideToConsents();
    return;
  }
  flow.goNext();
};
</script>

<template>
  <AStepPage :title="t('borrow.rules.title')" :step="flow.current.value" :total="flow.total.value">
    <ASection>
      <!-- 「取貨規定」這類分段標題用 h3，讀屏可以用標題跳段 -->
      <div :lang="zhAttr" class="flex flex-col gap-3 text-base">
        <template v-for="[k, v] in BORROW_RULES.items" :key="k">
          <h3 v-if="!v" class="tp-h3-semibold mt-2">{{ k }}</h3>
          <p v-else>
            <span class="font-semibold">{{ k }}</span>
            <span>{{ v }}</span>
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
          <!-- 電話可以直接撥打，也不在號碼中間斷行 -->
          <button
            type="button"
            class="a11y-focus -my-1 flex min-h-11 items-center whitespace-nowrap font-semibold text-primary-700 underline"
            @click="native.callPhone(c.phone)"
          >
            {{ c.phone }}
          </button>
        </li>
      </ul>
    </ASection>

    <ASection>
      <AChoice
        v-model="checked"
        :field-id="CONSENT_ID"
        class="scroll-mt-4"
        multiple
        required
        :legend="t('borrow.rules.consentIntro')"
        :hint="t('borrow.rules.consentNote')"
        :error="error"
        :options="BORROW_RULES.consents.map((a) => ({ value: a, label: a, lang: zhAttr }))"
        @update:model-value="hasError = false"
      />
    </ASection>

    <template #footer>
      <div class="grid grid-cols-2 gap-2">
        <BaseButton outline link :route-info="{ name: 'assistive-home' }">
          {{ t('borrow.rules.disagree') }}
        </BaseButton>
        <BaseButton @click="agree">{{ t('borrow.rules.agree') }}</BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
