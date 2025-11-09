<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import FilterChip from '@/components/sporta/filterChip.vue'
import EventCard from '@/components/sporta/card.vue'
import EventPair from '@/components/sporta/EventPair.vue'
import { fetchCategories, fetchLocations, realSearchEvents } from '@/utils/filtermock.js'
import { useSportaStore } from '@/stores/sporta'
import { useConnectionMessage } from '@/composables/useConnectionMessage'
import { useHandleConnectionData } from '@/composables/useHandleConnectionData'
const sportaStore = useSportaStore()
const q = ref('')
const activeCategory = ref('')
const activeLocation = ref('')
const results = ref([])
const loading = ref(true)
const pairOpen = ref(false)

// Make categories and locations reactive to store changes
const categories = computed(() => sportaStore.categories)
const locations = computed(() => sportaStore.locations)

useConnectionMessage('location',null)
useHandleConnectionData((event:{data:string})=>{
    const result = JSON.parse(event.data);
    sportaStore.curLocation = result.data
});
async function loadActualData() {
  await sportaStore.fetchCategories()
  await sportaStore.fetchLocations()
}
async function runSearch() {
  loading.value = true
  results.value = await realSearchEvents({
    q: q.value.trim(),
    category: activeCategory.value,
    location: activeLocation.value
  })
  loading.value = false
}

function clearCategory() { activeCategory.value = '' }
function clearLocation() { activeLocation.value = '' }
 
// Function to handle "目前最近" (Current Nearest) selection
async function selectNearestLocation() {
  console.log('Finding nearest locations...')
  // Use current location from store if available
  if (sportaStore.curLocation) {
    console.log('Current location:', sportaStore.curLocation)
    // Set activeLocation to a special value to indicate nearest search
    activeLocation.value = 'nearest'
    // Use nearestEventCoordinates when 目前最近 is chosen
    await sportaStore.changeToNearest()
    // The nearestEventCoordinates will be populated in the store
  } else {
    console.log('No current location available')
    // Could show a message to request location permission
    alert('無法取得目前位置，請確認位置權限已開啟')
    // Return to main (clear filters)
    activeLocation.value = ''
    activeCategory.value = ''
    q.value = ''
  }
}

onMounted(async () => {
  await loadActualData()
  await runSearch()
})

watch([q, activeCategory, activeLocation], () => {
  // Debounce (very light)
  clearTimeout(runSearch._t)
  runSearch._t = setTimeout(runSearch, 180)
})

const hasFilter = computed(() => !!(activeCategory.value || activeLocation.value || q.value.trim()))

function onDecide(selectedEvent) {
  console.log('User decided on event:', selectedEvent)
  // Handle the decision logic here
}

// Create lookup functions for proper name resolution
const getCategoryName = (categoryId) => {
  const category = sportaStore.categories.find(c => c.id === categoryId)
  return category ? category.name : categoryId
}

const getLocationName = (locationId) => {
  const location = sportaStore.locations.find(l => l.id === locationId)
  return location ? location.name : locationId
}

// Process results to ensure proper display names
const processedResults = computed(() => {
  return results.value.map(event => ({
    ...event,
    categoryName: getCategoryName(event.category),
    locationName: getLocationName(event.location)
  }))
})

// Computed property to get the events to display
const eventsToDisplay = computed(() => {
  if (activeLocation.value === 'nearest') {
    // Use nearestEventCoordinates when 目前最近 is selected
    return sportaStore.nearestEventCoordinates
  } else {
    // Return to main events list
    return sportaStore.events
  }
})
async function eventPairFetcher() {
  await sportaStore.fetchEvents()
  const events = sportaStore.events
  
  // Get random pair of events
  const shuffled = [...events].sort(() => 0.5 - Math.random())
  const items = shuffled.slice(0, 2).map(event => ({
    id: event.id,
    title: event.title,
    image: event.image, // Use image from sporta store
    location: event.location,
    time: event.starttime,
    host: event.organizer,
    tags: [event.category], // Convert single category to array
    exp: 1000 + Math.floor(Math.random() * 2000) // Mock exp for now
  }))
  
  return { items }
}
</script>

<template>
  <section class="px-4 py-6">
    <!-- 搜尋欄 -->
    <div class="bg-white rounded-2xl shadow-card p-3 flex items-center gap-3 mb-4">
      <button class="w-10 h-10 rounded-xl bg-secondary-50 border border-secondary-200 flex items-center justify-center" @click="pairOpen = true" aria-label="Open Event Pair">
        <svg viewBox="0 0 24 24" class="w-5 h-5 fill-secondary-500"><path d="M12 2l3.1 6.3 6.9 1-5 4.8 1.2 6.9L12 17.8 5.8 21l1.2-6.9-5-4.8 6.9-1z"/></svg>
      </button>
      <input
        class="flex-1 outline-none text-grey-800 placeholder-grey-400"
        v-model="q"
        type="search"
        inputmode="search"
        placeholder="搜尋活動"
        aria-label="Search events"
      />
      <button class="w-10 h-10 rounded-xl bg-primary-50 border border-primary-200 flex items-center justify-center" aria-label="Search" @click="runSearch">
        <svg viewBox="0 0 24 24" class="w-5 h-5 stroke-primary-500" fill="none" stroke-width="2"><path d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15z"/></svg>
      </button>
    </div>

    <!-- Category chips（可滑動） -->
    <div class="flex overflow-x-auto gap-2 pb-2 mb-4 scrollbar-hide">
      <FilterChip
        label="全部"
        :active="activeCategory===''"
        @click="clearCategory"
      />
      <FilterChip
        v-for="c in categories"
        :key="c.id"
        :label="c.name"
        :active="activeCategory===c.id"
        @click="activeCategory = (activeCategory===c.id ? '' : c.id)"
      />
    </div>

    <!-- Location chips（可滑動） -->
    <div class="flex overflow-x-auto gap-2 pb-2 mb-6 scrollbar-hide">
      <FilterChip
        label="所有地點"
        :active="activeLocation===''"
        @click="clearLocation"
      />
      <FilterChip
        label="目前最近"
        :active="activeLocation==='nearest'"
        @click="selectNearestLocation"
      />
      <FilterChip
        v-for="l in locations"
        :key="l.id"
        :label="l.name"
        :active="activeLocation===l.id"
        @click="activeLocation = (activeLocation===l.id ? '' : l.id)"
      />
    </div>

    <!-- 最近活動 / 搜尋結果 -->
    <header class="flex items-baseline justify-between px-2 mb-4">
      <h2 class="text-lg font-bold text-grey-800">最近活動</h2>
      <small v-if="hasFilter" class="text-grey-400 text-sm">已篩選</small>
    </header>

    <div v-if="loading" class="text-grey-400 text-center py-8">載入中…</div>
    <div v-else class="space-y-3">
      <EventCard v-for="e in eventsToDisplay" :key="e.id" :event="e" />
      <p v-if="!eventsToDisplay.length" class="text-grey-400 text-center py-8">無搜尋結果</p>
    </div>

    <div class="h-24"></div>
  </section>
  <EventPair v-model="pairOpen" :fetcher="eventPairFetcher" @decide="onDecide" />
</template>

<style scoped>
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
