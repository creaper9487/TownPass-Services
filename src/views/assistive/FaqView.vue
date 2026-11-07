<script setup lang="ts">
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import { faq } from '@/utils/assistive/faq';
</script>

<template>
  <AStepPage title="常見問題" lead="借用、預約、候補、取消與庫存的規則，都在這裡。">
    <ASection grey>
      <ul class="flex flex-col gap-3">
        <li v-for="item in faq" :key="item.q" class="tp-card">
          <details class="group">
            <summary
              class="a11y-focus flex min-h-14 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3"
            >
              <span class="tp-h3-semibold">{{ item.q }}</span>
              <img
                src="@/assets/images/down-icon.svg"
                alt=""
                class="h-6 w-6 shrink-0 transition-transform motion-reduce:transition-none group-open:rotate-180"
              />
            </summary>
            <p class="px-4 pb-4 text-sm text-grey-700">{{ item.a }}</p>
          </details>
        </li>
      </ul>
    </ASection>
  </AStepPage>
</template>
