<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import FilterChip from '@/components/sporta/filterChip.vue'
import EventCard from '@/components/sporta/card.vue'
import { fetchCategories, fetchLocations, searchEvents } from '@/utils/filtermock.js'

const q = ref('')
const categories = ref([])
const locations = ref([])
const activeCategory = ref('')
const activeLocation = ref('')
const results = ref([])
const loading = ref(true)

async function loadMeta() {
  const [cs, ls] = await Promise.all([fetchCategories(), fetchLocations()])
  categories.value = cs
  locations.value = ls
}

async function runSearch() {
  loading.value = true
  results.value = await searchEvents({
    q: q.value.trim(),
    category: activeCategory.value,
    location: activeLocation.value
  })
  loading.value = false
}

function clearCategory() { activeCategory.value = '' }
function clearLocation() { activeLocation.value = '' }

onMounted(async () => {
  await loadMeta()
  await runSearch()
})

watch([q, activeCategory, activeLocation], () => {
  // Debounce (very light)
  clearTimeout(runSearch._t)
  runSearch._t = setTimeout(runSearch, 180)
})

const hasFilter = computed(() => !!(activeCategory.value || activeLocation.value || q.value.trim()))
</script>

<template>
  <section class="search-page">
    <!-- 搜尋欄 -->
    <div class="search-bar glass">
      <button class="left-ico" aria-label="Saved">
        <!-- star icon -->
        <svg viewBox="0 0 24 24" class="ico"><path d="m12 17.3-5.6 3 1.1-6.3L3 9.7l6.3-.9L12 3l2.7 5.8 6.3.9-4.5 4.3 1.1 6.3z"/></svg>
      </button>
      <input
        class="input"
        v-model="q"
        type="search"
        inputmode="search"
        placeholder="Search events"
        aria-label="Search events"
      />
      <button class="right-ico" aria-label="Search" @click="runSearch">
        <!-- magnifier -->
        <svg viewBox="0 0 24 24" class="ico"><path d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15z"/></svg>
      </button>
    </div>

    <!-- Category chips（可滑動） -->
    <div class="hscroll">
      <FilterChip
        label="All"
        :active="activeCategory===''"
        @click="clearCategory"
      />
      <FilterChip
        v-for="c in categories"
        :key="c"
        :label="c"
        :active="activeCategory===c"
        @click="activeCategory = (activeCategory===c ? '' : c)"
      />
    </div>

    <!-- Location chips（可滑動） -->
    <div class="hscroll big">
      <FilterChip
        label="All locations"
        :active="activeLocation===''"
        @click="clearLocation"
      />
      <FilterChip
        v-for="l in locations"
        :key="l"
        :label="l"
        :active="activeLocation===l"
        @click="activeLocation = (activeLocation===l ? '' : l)"
      />
    </div>

    <!-- 最近活動 / 搜尋結果 -->
    <header class="section-title">
      <h2>Recent events</h2>
      <small v-if="hasFilter" class="muted">Filtered</small>
    </header>

    <div v-if="loading" class="state">Loading…</div>
    <div v-else class="list">
      <EventCard v-for="e in results" :key="e.id" :event="e" />
      <p v-if="!results.length" class="state">No result</p>
    </div>

    <div class="spacer"></div>
  </section>
</template>

<style scoped>
.search-page { padding: 0 4px; }

/* 玻璃輸入條 */
.glass {
  background: linear-gradient(180deg, rgba(255,255,255,.25), rgba(255,255,255,.14));
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  backdrop-filter: blur(var(--blur));
  -webkit-backdrop-filter: blur(var(--blur));
  box-shadow: 0 10px 30px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.25);
}

.search-bar {
  display: grid;
  grid-template-columns: 40px 1fr 40px;
  align-items: center;
  padding: 6px 6px 6px 8px;
  margin: 8px 4px 10px;
}
.input {
  appearance: none; border: 0; outline: none; background: transparent; color: var(--text);
  width: 100%; font-size: 15px;
}
.input::placeholder { color: var(--muted); }
.left-ico, .right-ico {
  -webkit-tap-highlight-color: transparent;
  appearance: none; border: 0; background: rgba(255,255,255,.16);
  width: 32px; height: 32px; border-radius: 10px;
  display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255,255,255,.28);
}
.right-ico { justify-self: end; }
.ico { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.6; color: #0e0f12; }

/* 橫向滑動 chips */
.hscroll {
  display: flex; overflow-x: auto; gap: 0; padding: 6px 4px 2px; margin-bottom: 8px;
  scroll-snap-type: x proximity;
}
.hscroll::-webkit-scrollbar { display: none; }
.hscroll > * { scroll-snap-align: start; }
.hscroll.big .chip { padding: 10px 14px; border-radius: 16px; }

/* 區段標題 */
.section-title {
  display: flex; align-items: baseline; justify-content: space-between;
  padding: 4px 8px 6px;
}
.section-title h2 { margin: 0; font-size: 16px; }
.muted { color: var(--muted); }

/* 結果清單 */
.list { display: grid; gap: 12px; }
.state { color: var(--muted); padding: 16px 8px; text-align: center; }

.spacer { height: 96px; }
</style>
