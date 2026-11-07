<script setup lang="ts">
import { RouterLink } from 'vue-router';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { stepRoute } from '@/composables/useAssistiveFlow';
import { t } from '@/i18n/assistive';

// 選輔具時固定在底部的「本次預約項目」：按「預約」加入後留在原頁，可以再選別的，
// 選好了直接「下一步」選中心，不必先經過一頁清單。點件數可以看清單、刪除。
const store = useAssistiveStore();
</script>

<template>
  <div class="flex items-center gap-3">
    <RouterLink
      :to="{ name: 'assistive-cart', params: { service: 'borrow' } }"
      class="a11y-focus flex min-h-12 flex-1 flex-col justify-center rounded-lg px-2 text-left"
    >
      <span class="text-sm text-grey-700">{{ t('borrow.cart.title') }}</span>
      <!-- 加入或刪除時讀屏會念出新的件數 -->
      <span aria-live="polite" class="text-base font-semibold text-primary-700 underline">
        {{ t('borrow.items.cartCount', { n: store.variants.length }) }}
      </span>
    </RouterLink>
    <BaseButton class="shrink-0 px-8" link :route-info="stepRoute('borrow', 'center')">
      {{ t('common.next') }}
    </BaseButton>
  </div>
</template>
