<script setup lang="ts">
import { onMounted } from 'vue';
import EventCard from '@/components/sporta/card.vue'
import { useSportaStore } from '@/stores/sporta';

const sportaStore = useSportaStore();

onMounted(async () => {
  // Initialize with a default user ID or get from auth
  if (sportaStore.userEvent.length === 0) {
    await sportaStore.fetchAllData("7f3562f4-bb3f-4ec7-89b9-da3b4b5ff250");
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
