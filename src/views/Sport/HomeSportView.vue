<script setup>
import { onMounted, ref } from 'vue'
import EventCard from '@/components/sporta/card.vue'
import {fetchEvents} from "@/utils/eventsmock"
const events = ref([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    events.value = await fetchEvents()
  } catch (e) {
    error.value = 'Failed to load events.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="home-wrap">
    <header class="intro">
      <h1 class="h1">運動活動</h1>
      <p class="sub">最新的城市運動清單</p>
    </header>

    <div v-if="loading" class="state">Loading…</div>
    <div v-else-if="error" class="state error">{{ error }}</div>

    <div v-else class="list">
      <EventCard v-for="e in events" :key="e.id" :event="e" />
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
