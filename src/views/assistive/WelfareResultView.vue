<script setup lang="ts">
import { useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { OFFICIAL_SITE, welfare } from '@/utils/assistive/welfare';

const router = useRouter();
const native = useAssistiveNative();

const open = (item: { page?: string; href?: string }) => {
  if (item.page) router.push({ name: 'assistive-welfare-page', params: { slug: item.page } });
  else if (item.href)
    native.openLink(item.href.startsWith('/') ? OFFICIAL_SITE + item.href : item.href);
};
</script>

<template>
  <AStepPage :title="welfare.result.title">
    <ASection>
      <p class="text-base">{{ welfare.result.text }}</p>
      <ul class="mt-4 divide-y divide-grey-100">
        <li v-for="(item, i) in welfare.result.items" :key="i">
          <button
            type="button"
            class="a11y-focus flex min-h-14 w-full items-center justify-between gap-3 py-3 text-left text-base"
            @click="open(item)"
          >
            <span class="font-semibold">{{ item.title }}</span>
            <img src="@/assets/images/down-icon.svg" alt="" class="h-6 w-6 shrink-0 -rotate-90" />
          </button>
        </li>
      </ul>
    </ASection>
    <template #footer>
      <BaseButton outline class="w-full" link :route-info="{ name: 'assistive-welfare' }">
        重新填答
      </BaseButton>
    </template>
  </AStepPage>
</template>
