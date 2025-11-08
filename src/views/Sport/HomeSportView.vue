<script setup lang="ts">
import { onMounted } from 'vue';
import EventCard from '@/components/sporta/card.vue'
import { useSportaStore } from '@/stores/sporta';

const sportaStore = useSportaStore();

onMounted(async () => {
  // Initialize with a default user ID or get from auth
  if (sportaStore.userEvent.length === 0) {
    await sportaStore.fetchAllData('default_user');
  }
});
</script>

<template>
  <section class="home-wrap">
    <header class="intro">
      <h1 class="h1">運動活動</h1>
      <p class="sub">最新的城市運動清單</p>
    </header>

    <div class="list">
      <EventCard v-for="e in sportaStore.userEvent" :key="e.id" :event="e" />
    </div>

    <div class="spacer"></div>
  </section>
</template>

<style scoped>
.home-wrap { padding: 0 4px; }
.intro { padding: 6px 8px 10px; }
.h1 { margin: 0; font-size: 20px; }
.sub { margin: 4px 0 0; color: var(--muted); font-size: 13px; }

.list { display: grid; gap: 12px; }
.state { color: var(--muted); padding: 20px 8px; }
.state.error { color: #ff8585; }
.spacer { height: 96px; }
</style>
