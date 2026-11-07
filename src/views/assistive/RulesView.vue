<script setup lang="ts">
import { computed, ref } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AChoice from '@/components/assistive/AChoice.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { t, zhAttr } from '@/i18n/assistive';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow } from '@/composables/useAssistiveFlow';
import { officialCenterRows } from '@/utils/assistive/centers';
import { BORROW_RULES } from '@/utils/assistive/services';

// 官方「二手輔具借用須知」：原文照登，三項同意都勾選後按「我同意」。
const store = useAssistiveStore();
const flow = useAssistiveFlow();

const checked = ref(BORROW_RULES.consents.filter((_, i) => store.consents[i]));
const hasError = ref(false);
const error = computed(() => (hasError.value ? t('borrow.rules.consentError') : ''));

const agree = () => {
  store.consents = BORROW_RULES.consents.map((a) => checked.value.includes(a));
  if (!store.consents.every(Boolean)) {
    hasError.value = true;
    return;
  }
  flow.goNext();
};
</script>

<template>
  <AStepPage :title="t('borrow.rules.title')" :step="flow.current.value" :total="flow.total.value">
    <ASection>
      <dl :lang="zhAttr" class="flex flex-col gap-3 text-base">
        <div v-for="[k, v] in BORROW_RULES.items" :key="k">
          <dt v-if="!v" class="tp-h3-semibold mt-2">{{ k }}</dt>
          <template v-else>
            <dt class="inline font-semibold">{{ k }}</dt>
            <dd class="inline">{{ v }}</dd>
          </template>
        </div>
      </dl>
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
          <p>{{ c.phone }}</p>
        </li>
      </ul>
    </ASection>

    <ASection>
      <AChoice
        v-model="checked"
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
