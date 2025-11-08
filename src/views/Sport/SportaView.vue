<script setup lang="ts">
import { ref } from 'vue'
import HomeView from '@/views/Sport/HomeSportView.vue'
import SearchView from './SearchView.vue'
import NotificationView from './NotificationView.vue';
import LeaderboardView from './LeaderboardView.vue';
import { computed } from 'vue';
import { useSportaStore, type userInfo } from '@/stores/sporta';
import { useConnectionMessage } from '@/composables/useConnectionMessage';
import { useHandleConnectionData } from '@/composables/useHandleConnectionData';
import AddEventSheet from '@/components/sporta/AddEventSheet.vue'

const sportaStore = useSportaStore();

useConnectionMessage('userinfo', null);

useHandleConnectionData((event: { data: string }) => {
    const result = JSON.parse(event.data);
    sportaStore.user.userID = result.data.id
});

sportaStore.fetchAllData(sportaStore.user.userID);
const tabs = [
  { key: 'home',     label: 'Home',     icon: 'home' },
  { key: 'search',   label: 'Search',   icon: 'search' },
  { key: 'add',      label: 'Add',      icon: 'plus' },
  { key: 'notify',   label: 'Alerts',   icon: 'bell' },
  { key: 'star',     label: 'Saved',    icon: 'star' },
]
const current = ref('home')
const showAdd = ref(false)

function setTab(k) {
  if (k === 'add') {
    showAdd.value = true // 直接開啟底部表單
  } else {
    current.value = k
  }
}

function onCreated() {
  showAdd.value = false
  // Optionally refresh the event list
  sportaStore.fetchAllData(sportaStore.user.userID)
}
</script>

<template>
  <div class="min-h-screen bg-grey-50">
    <div class="max-w-screen-lg mx-auto">
      <main class="pb-24">
        <!-- 分頁內容 -->
        <HomeView v-if="current==='home'" />
        <SearchView v-else-if="current==='search'" />
        <LeaderboardView v-else-if="current==='star'" />
        <NotificationView v-else-if="current==='notify'" />
        <!-- 其他分頁留白，未來補 -->
        <section v-else class="px-4 py-8">
          <div class="bg-white rounded-2xl shadow-card p-6 text-center">
            <p class="text-grey-400">Coming soon…</p>
          </div>
        </section>
      </main>

      <!-- 底部導覽 -->
      <nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-grey-200 shadow-lg">
        <div class="max-w-screen-lg mx-auto px-4 py-2 safe-area-inset-bottom">
          <div class="flex justify-around items-center">
            <button
              v-for="t in tabs"
              :key="t.key"
              class="flex flex-col items-center justify-center py-2 px-3 rounded-xl transition-all duration-200"
              :class="{ 
                'text-primary-500': current === t.key && t.key !== 'add',
                'text-grey-400': current !== t.key && t.key !== 'add',
                'bg-orange-50': t.key === 'add'
              }"
              @click="setTab(t.key)"
              :aria-label="t.label"
            >
              <svg 
                v-if="t.icon==='home'" 
                viewBox="0 0 24 24" 
                class="w-6 h-6 mb-1"
                :class="t.key === 'add' ? 'stroke-orange-500' : ''"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>
              </svg>
              <svg 
                v-else-if="t.icon==='search'" 
                viewBox="0 0 24 24" 
                class="w-6 h-6 mb-1"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15z"/>
              </svg>
              <svg 
                v-else-if="t.icon==='plus'" 
                viewBox="0 0 24 24" 
                class="w-6 h-6 mb-1 stroke-orange-500"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M12 5v14M5 12h14"/>
              </svg>
              <svg 
                v-else-if="t.icon==='bell'" 
                viewBox="0 0 24 24" 
                class="w-6 h-6 mb-1"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M6 8a6 6 0 1 1 12 0c0 7 3 6 3 8H3c0-2 3-1 3-8m6 13a3 3 0 0 1-3-3h6a3 3 0 0 1-3 3z"/>
              </svg>
              <svg 
                v-else 
                viewBox="0 0 24 24" 
                class="w-6 h-6 mb-1"
                :fill="current === t.key ? 'currentColor' : 'none'"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="m12 17.3-5.6 3 1.1-6.3L3 9.7l6.3-.9L12 3l2.7 5.8 6.3.9-4.5 4.3 1.1 6.3z"/>
              </svg>
              <span class="text-xs font-medium">{{ t.label }}</span>
            </button>
          </div>
        </div>
      </nav>
      <AddEventSheet v-model="showAdd" @created="onCreated" />
    </div>
  </div>
</template>



<style scoped>
.safe-area-inset-bottom {
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
</style>
