<script setup>
import { ref, computed, onMounted } from 'vue'

/**
 * Upgrade hooks:
 * - Replace `loadMock()` with real API (REST/GraphQL) in `fetchLeaderboard`
 * - Support pagination via `cursor` in state and `loadMore()`
 * - Add live updates (WebSocket/SSE) to push changes
 * - Add filters (e.g., friends-only, this week, global) via `scope` & `period`
 * - Local cache hydration via IndexedDB if needed
 */

// --------- state ---------
const loading = ref(true)
const error = ref('')
const entries = ref([]) // { id, name, avatar, exp, delta? }

// Mock loader
function loadMock() {
  // Deterministic but "random-looking" avatars & exps
  const base = [
    { id: 1, name: 'Ava',   avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ava',   exp: 28950 },
    { id: 2, name: 'Liam',  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Liam',  exp: 27510 },
    { id: 3, name: 'Mia',   avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mia',   exp: 26340 },
    { id: 4, name: 'Noah',  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Noah',  exp: 24180 },
    { id: 5, name: 'Emma',  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emma',  exp: 23990 },
    { id: 6, name: 'Mason', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mason', exp: 23340 },
    { id: 7, name: 'Luna',  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Luna',  exp: 22870 },
    { id: 8, name: 'Evan',  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Evan',  exp: 21920 },
    { id: 9, name: 'Zoe',   avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Zoe',   exp: 21340 },
    { id: 10,name: 'Aria',  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Aria',  exp: 20750 },
  ]
  return base.sort((a,b)=>b.exp-a.exp)
}

async function fetchLeaderboard() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch('http://192.168.22.42:8000/api/user/rankings/all')
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`)
    }
    const data = await res.json()
    // Transform API data to match component format
    entries.value = data.map(item => ({
      id: item.user_id,
      name: item.user_id,
      avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${item.user_id}`,
      exp: item.exp
    }))
  } catch (e) {
    console.error('Failed to load leaderboard:', e)
    error.value = 'Failed to load leaderboard.'
    // Fallback to mock data if API fails
    entries.value = loadMock()
  } finally {
    loading.value = false
  }
}

onMounted(fetchLeaderboard)

// --------- derived ---------
const top3 = computed(() => entries.value.slice(0,3))
const rest = computed(() => entries.value.slice(3))
</script>

<template>
  <div class="px-4 py-6">
    <header class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-grey-800">排行榜</h1>
      <button 
        class="w-10 h-10 rounded-xl bg-white border border-grey-200 flex items-center justify-center shadow-sm active:scale-95 transition-transform" 
        title="重新整理" 
        @click="fetchLeaderboard" 
        :disabled="loading"
      >
        <svg viewBox="0 0 24 24" class="w-5 h-5 stroke-primary-500" fill="none" stroke-width="2">
          <path d="M3 12a9 9 0 0 1 15.3-6.3l1.7-1.7v6h-6l2.2-2.2A7 7 0 1 0 19 12h2a9 9 0 1 1-18 0z"/>
        </svg>
      </button>
    </header>

    <!-- Podium -->
    <section class="mb-6" aria-label="前三名">
      <div class="grid grid-cols-3 gap-3 items-end">
        <!-- 第二名 -->
        <div class="bg-white rounded-2xl shadow-card p-3 text-center border border-grey-100" v-if="top3[1]">
          <div class="w-14 h-14 rounded-full overflow-hidden mx-auto mb-2 border-2 border-white shadow-md">
            <img :src="top3[1].avatar" :alt="top3[1].name" class="w-full h-full object-cover" />
          </div>
          <div class="font-bold text-sm text-grey-800">{{ top3[1].name }}</div>
          <div class="text-xs text-grey-400 mt-1">{{ top3[1].exp.toLocaleString() }} EXP</div>
          <div class="mt-2 h-12 bg-gradient-to-b from-grey-100 to-grey-200 rounded-xl flex items-center justify-center border border-grey-300">
            <span class="font-black text-grey-700">2</span>
          </div>
        </div>

        <!-- 第一名 -->
        <div class="bg-white rounded-2xl shadow-card p-3 text-center border border-secondary-200 -mt-2" v-if="top3[0]">
          <div class="text-2xl mb-1">👑</div>
          <div class="w-16 h-16 rounded-full overflow-hidden mx-auto mb-2 border-2 border-secondary-300 shadow-lg ring-4 ring-secondary-100">
            <img :src="top3[0].avatar" :alt="top3[0].name" class="w-full h-full object-cover" />
          </div>
          <div class="font-bold text-sm text-grey-800">{{ top3[0].name }}</div>
          <div class="text-xs text-grey-400 mt-1">{{ top3[0].exp.toLocaleString() }} EXP</div>
          <div class="mt-2 h-16 bg-gradient-to-b from-secondary-300 to-secondary-400 rounded-xl flex items-center justify-center border border-secondary-500">
            <span class="font-black text-lg text-grey-800">1</span>
          </div>
        </div>

        <!-- 第三名 -->
        <div class="bg-white rounded-2xl shadow-card p-3 text-center border border-grey-100" v-if="top3[2]">
          <div class="w-14 h-14 rounded-full overflow-hidden mx-auto mb-2 border-2 border-white shadow-md">
            <img :src="top3[2].avatar" :alt="top3[2].name" class="w-full h-full object-cover" />
          </div>
          <div class="font-bold text-sm text-grey-800">{{ top3[2].name }}</div>
          <div class="text-xs text-grey-400 mt-1">{{ top3[2].exp.toLocaleString() }} EXP</div>
          <div class="mt-2 h-12 bg-gradient-to-b from-orange-200 to-orange-300 rounded-xl flex items-center justify-center border border-orange-400">
            <span class="font-black text-grey-700">3</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 排行列表 -->
    <section aria-label="第4名以後">
      <div class="space-y-2">
        <article
          v-for="(e, i) in rest"
          :key="e.id"
          class="bg-white rounded-2xl shadow-card p-3 flex items-center gap-3 border border-grey-100"
        >
          <div class="w-9 h-9 rounded-xl bg-primary-50 border border-primary-100 flex items-center justify-center font-black text-sm text-primary-600">
            {{ i + 4 }}
          </div>
          <img class="w-10 h-10 rounded-full object-cover border-2 border-white shadow-sm" :src="e.avatar" :alt="e.name" />
          <div class="flex-1 min-w-0">
            <div class="font-bold text-sm text-grey-800 truncate">{{ e.name }}</div>
          </div>
          <div class="font-bold text-sm text-grey-800">
            {{ e.exp.toLocaleString() }}<span class="text-grey-400 text-xs ml-1">EXP</span>
          </div>
        </article>
      </div>

      <div v-if="loading" class="space-y-3 mt-4">
        <div class="h-14 rounded-2xl bg-grey-100 animate-pulse" v-for="i in 5" :key="i"></div>
      </div>
      <p v-if="error" class="text-warn-200 font-bold text-center mt-4">{{ error }}</p>
    </section>

    <div class="h-24"></div>
  </div>
</template>

<style scoped></style>
