<script setup>
import { eventInfo } from '@/stores/sporta';

defineProps({
  event: {
    type: eventInfo,
    required: true,
  },
});
</script>

<template>
  <article class="event-card">
    <div class="cover-wrap">
      <img class="cover" :src="event.cover" :alt="event.title" loading="lazy" />
    </div>

    <div class="meta">
      <h3 class="title">{{ event.title }}</h3>
      <div class="row">
        <svg viewBox="0 0 24 24" class="i"><path d="M6 2h12a2 2 0 0 1 2 2v16l-8-4-8 4V4a2 2 0 0 1 2-2z"/></svg>
        <span>{{ event.organizer }}</span>
      </div>
      <div class="row">
        <svg viewBox="0 0 24 24" class="i"><path d="M6 8h12M6 12h12M6 16h12"/></svg>
        <span>{{ event.starttime }}</span>
      </div>
      <div class="row">
        <svg viewBox="0 0 24 24" class="i"><path d="M12 21s-7-4.5-7-10a7 7 0 1 1 14 0c0 5.5-7 10-7 10z"/><circle cx="12" cy="11" r="3"/></svg>
        <span>{{ event.location }}</span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.event-card {
  border-radius: 18px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255,255,255,.22), rgba(255,255,255,.12));
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(var(--blur));
  -webkit-backdrop-filter: blur(var(--blur));
  box-shadow: 0 10px 30px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.25);
}

.cover-wrap { position: relative; aspect-ratio: 16/9; background: rgba(0,0,0,.3); }
.cover { width: 100%; height: 100%; object-fit: cover; display: block; }

.meta { padding: 12px 14px 14px; }
.title {
  margin: 0 0 8px;
  font-size: 16px; line-height: 1.3; letter-spacing: .2px;
}
.row {
  display: flex; align-items: center; gap: 8px;
  color: var(--muted);
  font-size: 13px;
  margin-top: 6px;
  min-height: 20px;
}
.i { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.6; }
</style>
