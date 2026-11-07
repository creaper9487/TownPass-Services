<script setup lang="ts">
import { computed, onMounted } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import AServiceCard from '@/components/assistive/AServiceCard.vue';
import ClosureNotice from '@/components/assistive/ClosureNotice.vue';
import ALanguageSwitch from '@/components/assistive/ALanguageSwitch.vue';
import welfareIcon from '@/assets/images/assistive/icon-welfare.svg';
import assessIcon from '@/assets/images/assistive/icon-assess.svg';
import reservationIcon from '@/assets/images/assistive/icon-reservation.svg';
import { useAssistiveStore } from '@/stores/assistive';
import { serviceTitle } from '@/utils/assistive/services';
import { t } from '@/i18n/assistive';
import { catalog } from '@/utils/assistive/catalog';

const store = useAssistiveStore();

// 借用卡片放官方品項照片（輪椅、助行器、拐杖）
const photos = computed(() =>
  catalog.value.filter((c) => ['輪椅', '助行器', '拐杖'].includes(c.name)).map((c) => c.image)
);

onMounted(() => store.loadCalendars());
</script>

<template>
  <AStepPage :title="t('app.title')" hide-header>
    <div class="flex flex-col gap-2 px-4 py-4">
      <ClosureNotice v-if="store.closureNotices.length" :items="store.closureNotices" />

      <nav :aria-label="t('home.menu')" class="flex flex-col gap-2">
        <AServiceCard
          class="a-rise"
          :style="{ '--i': 0 }"
          hero
          :title="serviceTitle('borrow')"
          :photos="photos"
          :to="{ name: 'assistive-rules', params: { service: 'borrow' } }"
          @click="store.begin('borrow')"
        />
        <AServiceCard
          class="a-rise"
          :style="{ '--i': 1 }"
          :title="t('home.welfare')"
          :icon="welfareIcon"
          :to="{ name: 'assistive-welfare' }"
        />
        <AServiceCard
          class="a-rise"
          :style="{ '--i': 2 }"
          :title="serviceTitle('assess')"
          :icon="assessIcon"
          :to="{ name: 'assistive-need', params: { service: 'assess' } }"
          @click="store.begin('assess')"
        />
        <AServiceCard
          class="a-rise"
          :style="{ '--i': 3 }"
          :title="t('home.reservations')"
          :icon="reservationIcon"
          :to="{ name: 'assistive-reservations' }"
        />
      </nav>

      <div class="mt-4">
        <ALanguageSwitch class="a-rise" :style="{ '--i': 4 }" />
      </div>
    </div>
  </AStepPage>
</template>
