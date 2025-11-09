<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue';
import EventCard from '@/components/sporta/card.vue'
import { useSportaStore } from '@/stores/sporta';

const sportaStore = useSportaStore();
const refreshInterval = ref<number | null>(null);

const refreshCards = async () => {
  try {
    await sportaStore.fetchAllData("7f3562f4-bb3f-4ec7-89b9-da3b4b5ff250");
    console.log('Cards refreshed successfully');
  } catch (error) {
    console.error('Error refreshing cards:', error);
  }
};

onMounted(async () => {
  // Initialize with a default user ID or get from auth
  if (sportaStore.userEvent.length === 0) {
    await sportaStore.fetchAllData("7f3562f4-bb3f-4ec7-89b9-da3b4b5ff250");
  }

  // Set up auto-refresh every 15 seconds
  refreshInterval.value = setInterval(refreshCards, 15000);
});

onBeforeUnmount(() => {
  // Clean up the interval when component is unmounted
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value);
    refreshInterval.value = null;
  }
});
</script>

<template>
  <section class="px-4 py-6">
    <header class="mb-6">
      <h1 class="text-2xl font-bold text-grey-800 mb-2">運動活動</h1>
      <p class="text-grey-400 text-sm">最新的城市運動清單</p>
    </header>

    <div class="space-y-3">
      <EventCard v-for="e in sportaStore.userEvent" :key="e.id" :event="e" />
    </div>

    <div class="h-24"></div>
  </section>
</template>

<style scoped></style>
