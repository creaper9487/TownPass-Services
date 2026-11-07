<script setup lang="ts">
import { onMounted } from 'vue';
import AStepPage from '@/components/assistive/AStepPage.vue';
import AServiceCard from '@/components/assistive/AServiceCard.vue';
import ClosureNotice from '@/components/assistive/ClosureNotice.vue';
import welfareIcon from '@/assets/images/assistive/icon-welfare.svg';
import assessIcon from '@/assets/images/assistive/icon-assess.svg';
import reservationIcon from '@/assets/images/assistive/icon-reservation.svg';
import { useAssistiveStore } from '@/stores/assistive';
import { services } from '@/utils/assistive/services';
import catalogJson from '@/data/assistive-catalog.json';
import type { Category } from '@/utils/assistive/types';

const store = useAssistiveStore();

// 借用卡片放官方品項照片（輪椅、助行器、拐杖）
const photos = (catalogJson as Category[])
  .filter((c) => ['輪椅', '助行器', '拐杖'].includes(c.name))
  .map((c) => c.image);

onMounted(() => store.loadCalendars());
</script>

<template>
  <AStepPage title="輔具預約" hide-header>
    <div class="flex flex-col gap-2 px-4 py-4">
      <ClosureNotice v-if="store.closureNotices.length" :items="store.closureNotices" />

      <nav aria-label="功能選單" class="flex flex-col gap-2">
        <AServiceCard
          hero
          :title="services.borrow.title"
          :photos="photos"
          :to="{ name: 'assistive-rules', params: { service: 'borrow' } }"
          @click="store.begin('borrow')"
        />
        <AServiceCard
          title="輔具福利查詢"
          :icon="welfareIcon"
          :to="{ name: 'assistive-welfare' }"
        />
        <AServiceCard
          :title="services.assess.title"
          :icon="assessIcon"
          :to="{ name: 'assistive-need', params: { service: 'assess' } }"
          @click="store.begin('assess')"
        />
        <AServiceCard
          title="服務預約查詢與取消"
          :icon="reservationIcon"
          :to="{ name: 'assistive-reservations' }"
        />
      </nav>
    </div>
  </AStepPage>
</template>
